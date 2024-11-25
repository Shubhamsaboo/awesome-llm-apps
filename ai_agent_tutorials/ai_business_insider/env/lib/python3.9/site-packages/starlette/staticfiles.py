from __future__ import annotations

import errno
import importlib.util
import os
import stat
import typing
from email.utils import parsedate

import anyio
import anyio.to_thread

from starlette._utils import get_route_path
from starlette.datastructures import URL, Headers
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, RedirectResponse, Response
from starlette.types import Receive, Scope, Send

PathLike = typing.Union[str, "os.PathLike[str]"]


class NotModifiedResponse(Response):
    NOT_MODIFIED_HEADERS = (
        "cache-control",
        "content-location",
        "date",
        "etag",
        "expires",
        "vary",
    )

    def __init__(self, headers: Headers):
        super().__init__(
            status_code=304,
            headers={name: value for name, value in headers.items() if name in self.NOT_MODIFIED_HEADERS},
        )


class StaticFiles:
    def __init__(
        self,
        *,
        directory: PathLike | None = None,
        packages: list[str | tuple[str, str]] | None = None,
        html: bool = False,
        check_dir: bool = True,
        follow_symlink: bool = False,
    ) -> None:
        self.directory = directory
        self.packages = packages
        self.all_directories = self.get_directories(directory, packages)
        self.html = html
        self.config_checked = False
        self.follow_symlink = follow_symlink
        if check_dir and directory is not None and not os.path.isdir(directory):
            raise RuntimeError(f"Directory '{directory}' does not exist")

    def get_directories(
        self,
        directory: PathLike | None = None,
        packages: list[str | tuple[str, str]] | None = None,
    ) -> list[PathLike]:
        """
        Given `directory` and `packages` arguments, return a list of all the
        directories that should be used for serving static files from.
        """
        directories = []
        if directory is not None:
            directories.append(directory)

        for package in packages or []:
            if isinstance(package, tuple):
                package, statics_dir = package
            else:
                statics_dir = "statics"
            spec = importlib.util.find_spec(package)
            assert spec is not None, f"Package {package!r} could not be found."
            assert spec.origin is not None, f"Package {package!r} could not be found."
            package_directory = os.path.normpath(os.path.join(spec.origin, "..", statics_dir))
            assert os.path.isdir(
                package_directory
            ), f"Directory '{statics_dir!r}' in package {package!r} could not be found."
            directories.append(package_directory)

        return directories

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        The ASGI entry point.
        """
        assert scope["type"] == "http"

        if not self.config_checked:
            await self.check_config()
            self.config_checked = True

        path = self.get_path(scope)
        response = await self.get_response(path, scope)
        await response(scope, receive, send)

    def get_path(self, scope: Scope) -> str:
        """
        Given the ASGI scope, return the `path` string to serve up,
        with OS specific path separators, and any '..', '.' components removed.
        """
        route_path = get_route_path(scope)
        return os.path.normpath(os.path.join(*route_path.split("/")))

    async def get_response(self, path: str, scope: Scope) -> Response:
        """
        Returns an HTTP response, given the incoming path, method and request headers.
        """
        if scope["method"] not in ("GET", "HEAD"):
            raise HTTPException(status_code=405)

        try:
            full_path, stat_result = await anyio.to_thread.run_sync(self.lookup_path, path)
        except PermissionError:
            raise HTTPException(status_code=401)
        except OSError as exc:
            # Filename is too long, so it can't be a valid static file.
            if exc.errno == errno.ENAMETOOLONG:
                raise HTTPException(status_code=404)

            raise exc

        if stat_result and stat.S_ISREG(stat_result.st_mode):
            # We have a static file to serve.
            return self.file_response(full_path, stat_result, scope)

        elif stat_result and stat.S_ISDIR(stat_result.st_mode) and self.html:
            # We're in HTML mode, and have got a directory URL.
            # Check if we have 'index.html' file to serve.
            index_path = os.path.join(path, "index.html")
            full_path, stat_result = await anyio.to_thread.run_sync(self.lookup_path, index_path)
            if stat_result is not None and stat.S_ISREG(stat_result.st_mode):
                if not scope["path"].endswith("/"):
                    # Directory URLs should redirect to always end in "/".
                    url = URL(scope=scope)
                    url = url.replace(path=url.path + "/")
                    return RedirectResponse(url=url)
                return self.file_response(full_path, stat_result, scope)

        if self.html:
            # Check for '404.html' if we're in HTML mode.
            full_path, stat_result = await anyio.to_thread.run_sync(self.lookup_path, "404.html")
            if stat_result and stat.S_ISREG(stat_result.st_mode):
                return FileResponse(full_path, stat_result=stat_result, status_code=404)
        raise HTTPException(status_code=404)

    def lookup_path(self, path: str) -> tuple[str, os.stat_result | None]:
        for directory in self.all_directories:
            joined_path = os.path.join(directory, path)
            if self.follow_symlink:
                full_path = os.path.abspath(joined_path)
            else:
                full_path = os.path.realpath(joined_path)
            directory = os.path.realpath(directory)
            if os.path.commonpath([full_path, directory]) != directory:
                # Don't allow misbehaving clients to break out of the static files
                # directory.
                continue
            try:
                return full_path, os.stat(full_path)
            except (FileNotFoundError, NotADirectoryError):
                continue
        return "", None

    def file_response(
        self,
        full_path: PathLike,
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        request_headers = Headers(scope=scope)

        response = FileResponse(full_path, status_code=status_code, stat_result=stat_result)
        if self.is_not_modified(response.headers, request_headers):
            return NotModifiedResponse(response.headers)
        return response

    async def check_config(self) -> None:
        """
        Perform a one-off configuration check that StaticFiles is actually
        pointed at a directory, so that we can raise loud errors rather than
        just returning 404 responses.
        """
        if self.directory is None:
            return

        try:
            stat_result = await anyio.to_thread.run_sync(os.stat, self.directory)
        except FileNotFoundError:
            raise RuntimeError(f"StaticFiles directory '{self.directory}' does not exist.")
        if not (stat.S_ISDIR(stat_result.st_mode) or stat.S_ISLNK(stat_result.st_mode)):
            raise RuntimeError(f"StaticFiles path '{self.directory}' is not a directory.")

    def is_not_modified(self, response_headers: Headers, request_headers: Headers) -> bool:
        """
        Given the request and response headers, return `True` if an HTTP
        "Not Modified" response could be returned instead.
        """
        try:
            if_none_match = request_headers["if-none-match"]
            etag = response_headers["etag"]
            if etag in [tag.strip(" W/") for tag in if_none_match.split(",")]:
                return True
        except KeyError:
            pass

        try:
            if_modified_since = parsedate(request_headers["if-modified-since"])
            last_modified = parsedate(response_headers["last-modified"])
            if if_modified_since is not None and last_modified is not None and if_modified_since >= last_modified:
                return True
        except KeyError:
            pass

        return False
