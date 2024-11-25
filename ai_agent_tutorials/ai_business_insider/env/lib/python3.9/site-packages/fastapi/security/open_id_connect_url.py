from typing import Optional

from fastapi.openapi.models import OpenIdConnect as OpenIdConnectModel
from fastapi.security.base import SecurityBase
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from typing_extensions import Annotated, Doc


class OpenIdConnect(SecurityBase):
    """
    OpenID Connect authentication class. An instance of it would be used as a
    dependency.
    """

    def __init__(
        self,
        *,
        openIdConnectUrl: Annotated[
            str,
            Doc(
                """
            The OpenID Connect URL.
            """
            ),
        ],
        scheme_name: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if no HTTP Authorization header is provided, required for
                OpenID Connect authentication, it will automatically cancel the request
                and send the client an error.

                If `auto_error` is set to `False`, when the HTTP Authorization header
                is not available, instead of erroring out, the dependency result will
                be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, with OpenID
                Connect or in a cookie).
                """
            ),
        ] = True,
    ):
        self.model = OpenIdConnectModel(
            openIdConnectUrl=openIdConnectUrl, description=description
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if not authorization:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return authorization
