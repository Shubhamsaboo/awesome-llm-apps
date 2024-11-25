from __future__ import annotations

import typing
import warnings
from os import PathLike

from starlette.background import BackgroundTask
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.types import Receive, Scope, Send

try:
    import jinja2

    # @contextfunction was renamed to @pass_context in Jinja 3.0, and was removed in 3.1
    # hence we try to get pass_context (most installs will be >=3.1)
    # and fall back to contextfunction,
    # adding a type ignore for mypy to let us access an attribute that may not exist
    if hasattr(jinja2, "pass_context"):
        pass_context = jinja2.pass_context
    else:  # pragma: no cover
        pass_context = jinja2.contextfunction  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    jinja2 = None  # type: ignore[assignment]


class _TemplateResponse(HTMLResponse):
    def __init__(
        self,
        template: typing.Any,
        context: dict[str, typing.Any],
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ):
        self.template = template
        self.context = context
        content = template.render(context)
        super().__init__(content, status_code, headers, media_type, background)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = self.context.get("request", {})
        extensions = request.get("extensions", {})
        if "http.response.debug" in extensions:
            await send(
                {
                    "type": "http.response.debug",
                    "info": {
                        "template": self.template,
                        "context": self.context,
                    },
                }
            )
        await super().__call__(scope, receive, send)


class Jinja2Templates:
    """
    templates = Jinja2Templates("templates")

    return templates.TemplateResponse("index.html", {"request": request})
    """

    @typing.overload
    def __init__(
        self,
        directory: str | PathLike[str] | typing.Sequence[str | PathLike[str]],
        *,
        context_processors: list[typing.Callable[[Request], dict[str, typing.Any]]] | None = None,
        **env_options: typing.Any,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        *,
        env: jinja2.Environment,
        context_processors: list[typing.Callable[[Request], dict[str, typing.Any]]] | None = None,
    ) -> None: ...

    def __init__(
        self,
        directory: str | PathLike[str] | typing.Sequence[str | PathLike[str]] | None = None,
        *,
        context_processors: list[typing.Callable[[Request], dict[str, typing.Any]]] | None = None,
        env: jinja2.Environment | None = None,
        **env_options: typing.Any,
    ) -> None:
        if env_options:
            warnings.warn(
                "Extra environment options are deprecated. Use a preconfigured jinja2.Environment instead.",
                DeprecationWarning,
            )
        assert jinja2 is not None, "jinja2 must be installed to use Jinja2Templates"
        assert bool(directory) ^ bool(env), "either 'directory' or 'env' arguments must be passed"
        self.context_processors = context_processors or []
        if directory is not None:
            self.env = self._create_env(directory, **env_options)
        elif env is not None:
            self.env = env

        self._setup_env_defaults(self.env)

    def _create_env(
        self,
        directory: str | PathLike[str] | typing.Sequence[str | PathLike[str]],
        **env_options: typing.Any,
    ) -> jinja2.Environment:
        loader = jinja2.FileSystemLoader(directory)
        env_options.setdefault("loader", loader)
        env_options.setdefault("autoescape", True)

        return jinja2.Environment(**env_options)

    def _setup_env_defaults(self, env: jinja2.Environment) -> None:
        @pass_context
        def url_for(
            context: dict[str, typing.Any],
            name: str,
            /,
            **path_params: typing.Any,
        ) -> URL:
            request: Request = context["request"]
            return request.url_for(name, **path_params)

        env.globals.setdefault("url_for", url_for)

    def get_template(self, name: str) -> jinja2.Template:
        return self.env.get_template(name)

    @typing.overload
    def TemplateResponse(
        self,
        request: Request,
        name: str,
        context: dict[str, typing.Any] | None = None,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> _TemplateResponse: ...

    @typing.overload
    def TemplateResponse(
        self,
        name: str,
        context: dict[str, typing.Any] | None = None,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> _TemplateResponse:
        # Deprecated usage
        ...

    def TemplateResponse(self, *args: typing.Any, **kwargs: typing.Any) -> _TemplateResponse:
        if args:
            if isinstance(args[0], str):  # the first argument is template name (old style)
                warnings.warn(
                    "The `name` is not the first parameter anymore. "
                    "The first parameter should be the `Request` instance.\n"
                    'Replace `TemplateResponse(name, {"request": request})` by `TemplateResponse(request, name)`.',
                    DeprecationWarning,
                )

                name = args[0]
                context = args[1] if len(args) > 1 else kwargs.get("context", {})
                status_code = args[2] if len(args) > 2 else kwargs.get("status_code", 200)
                headers = args[2] if len(args) > 2 else kwargs.get("headers")
                media_type = args[3] if len(args) > 3 else kwargs.get("media_type")
                background = args[4] if len(args) > 4 else kwargs.get("background")

                if "request" not in context:
                    raise ValueError('context must include a "request" key')
                request = context["request"]
            else:  # the first argument is a request instance (new style)
                request = args[0]
                name = args[1] if len(args) > 1 else kwargs["name"]
                context = args[2] if len(args) > 2 else kwargs.get("context", {})
                status_code = args[3] if len(args) > 3 else kwargs.get("status_code", 200)
                headers = args[4] if len(args) > 4 else kwargs.get("headers")
                media_type = args[5] if len(args) > 5 else kwargs.get("media_type")
                background = args[6] if len(args) > 6 else kwargs.get("background")
        else:  # all arguments are kwargs
            if "request" not in kwargs:
                warnings.warn(
                    "The `TemplateResponse` now requires the `request` argument.\n"
                    'Replace `TemplateResponse(name, {"context": context})` by `TemplateResponse(request, name)`.',
                    DeprecationWarning,
                )
                if "request" not in kwargs.get("context", {}):
                    raise ValueError('context must include a "request" key')

            context = kwargs.get("context", {})
            request = kwargs.get("request", context.get("request"))
            name = typing.cast(str, kwargs["name"])
            status_code = kwargs.get("status_code", 200)
            headers = kwargs.get("headers")
            media_type = kwargs.get("media_type")
            background = kwargs.get("background")

        context.setdefault("request", request)
        for context_processor in self.context_processors:
            context.update(context_processor(request))

        template = self.get_template(name)
        return _TemplateResponse(
            template,
            context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
