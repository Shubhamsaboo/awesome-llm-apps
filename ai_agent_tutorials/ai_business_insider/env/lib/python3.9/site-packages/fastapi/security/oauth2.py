from typing import Any, Dict, List, Optional, Union, cast

from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuth2 as OAuth2Model
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.param_functions import Form
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

# TODO: import from typing when deprecating Python 3.9
from typing_extensions import Annotated, Doc


class OAuth2PasswordRequestForm:
    """
    This is a dependency class to collect the `username` and `password` as form data
    for an OAuth2 password flow.

    The OAuth2 specification dictates that for a password flow the data should be
    collected using form data (instead of JSON) and that it should have the specific
    fields `username` and `password`.

    All the initialization parameters are extracted from the request.

    Read more about it in the
    [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).

    ## Example

    ```python
    from typing import Annotated

    from fastapi import Depends, FastAPI
    from fastapi.security import OAuth2PasswordRequestForm

    app = FastAPI()


    @app.post("/login")
    def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
        data = {}
        data["scopes"] = []
        for scope in form_data.scopes:
            data["scopes"].append(scope)
        if form_data.client_id:
            data["client_id"] = form_data.client_id
        if form_data.client_secret:
            data["client_secret"] = form_data.client_secret
        return data
    ```

    Note that for OAuth2 the scope `items:read` is a single scope in an opaque string.
    You could have custom internal logic to separate it by colon characters (`:`) or
    similar, and get the two parts `items` and `read`. Many applications do that to
    group and organize permissions, you could do it as well in your application, just
    know that that it is application specific, it's not part of the specification.
    """

    def __init__(
        self,
        *,
        grant_type: Annotated[
            Union[str, None],
            Form(pattern="password"),
            Doc(
                """
                The OAuth2 spec says it is required and MUST be the fixed string
                "password". Nevertheless, this dependency class is permissive and
                allows not passing it. If you want to enforce it, use instead the
                `OAuth2PasswordRequestFormStrict` dependency.
                """
            ),
        ] = None,
        username: Annotated[
            str,
            Form(),
            Doc(
                """
                `username` string. The OAuth2 spec requires the exact field name
                `username`.
                """
            ),
        ],
        password: Annotated[
            str,
            Form(),
            Doc(
                """
                `password` string. The OAuth2 spec requires the exact field name
                `password".
                """
            ),
        ],
        scope: Annotated[
            str,
            Form(),
            Doc(
                """
                A single string with actually several scopes separated by spaces. Each
                scope is also a string.

                For example, a single string with:

                ```python
                "items:read items:write users:read profile openid"
                ````

                would represent the scopes:

                * `items:read`
                * `items:write`
                * `users:read`
                * `profile`
                * `openid`
                """
            ),
        ] = "",
        client_id: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_id`, it can be sent as part of the form fields.
                But the OAuth2 specification recommends sending the `client_id` and
                `client_secret` (if any) using HTTP Basic auth.
                """
            ),
        ] = None,
        client_secret: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_password` (and a `client_id`), they can be sent
                as part of the form fields. But the OAuth2 specification recommends
                sending the `client_id` and `client_secret` (if any) using HTTP Basic
                auth.
                """
            ),
        ] = None,
    ):
        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


class OAuth2PasswordRequestFormStrict(OAuth2PasswordRequestForm):
    """
    This is a dependency class to collect the `username` and `password` as form data
    for an OAuth2 password flow.

    The OAuth2 specification dictates that for a password flow the data should be
    collected using form data (instead of JSON) and that it should have the specific
    fields `username` and `password`.

    All the initialization parameters are extracted from the request.

    The only difference between `OAuth2PasswordRequestFormStrict` and
    `OAuth2PasswordRequestForm` is that `OAuth2PasswordRequestFormStrict` requires the
    client to send the form field `grant_type` with the value `"password"`, which
    is required in the OAuth2 specification (it seems that for no particular reason),
    while for `OAuth2PasswordRequestForm` `grant_type` is optional.

    Read more about it in the
    [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).

    ## Example

    ```python
    from typing import Annotated

    from fastapi import Depends, FastAPI
    from fastapi.security import OAuth2PasswordRequestForm

    app = FastAPI()


    @app.post("/login")
    def login(form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()]):
        data = {}
        data["scopes"] = []
        for scope in form_data.scopes:
            data["scopes"].append(scope)
        if form_data.client_id:
            data["client_id"] = form_data.client_id
        if form_data.client_secret:
            data["client_secret"] = form_data.client_secret
        return data
    ```

    Note that for OAuth2 the scope `items:read` is a single scope in an opaque string.
    You could have custom internal logic to separate it by colon characters (`:`) or
    similar, and get the two parts `items` and `read`. Many applications do that to
    group and organize permissions, you could do it as well in your application, just
    know that that it is application specific, it's not part of the specification.


    grant_type: the OAuth2 spec says it is required and MUST be the fixed string "password".
        This dependency is strict about it. If you want to be permissive, use instead the
        OAuth2PasswordRequestForm dependency class.
    username: username string. The OAuth2 spec requires the exact field name "username".
    password: password string. The OAuth2 spec requires the exact field name "password".
    scope: Optional string. Several scopes (each one a string) separated by spaces. E.g.
        "items:read items:write users:read profile openid"
    client_id: optional string. OAuth2 recommends sending the client_id and client_secret (if any)
        using HTTP Basic auth, as: client_id:client_secret
    client_secret: optional string. OAuth2 recommends sending the client_id and client_secret (if any)
        using HTTP Basic auth, as: client_id:client_secret
    """

    def __init__(
        self,
        grant_type: Annotated[
            str,
            Form(pattern="password"),
            Doc(
                """
                The OAuth2 spec says it is required and MUST be the fixed string
                "password". This dependency is strict about it. If you want to be
                permissive, use instead the `OAuth2PasswordRequestForm` dependency
                class.
                """
            ),
        ],
        username: Annotated[
            str,
            Form(),
            Doc(
                """
                `username` string. The OAuth2 spec requires the exact field name
                `username`.
                """
            ),
        ],
        password: Annotated[
            str,
            Form(),
            Doc(
                """
                `password` string. The OAuth2 spec requires the exact field name
                `password".
                """
            ),
        ],
        scope: Annotated[
            str,
            Form(),
            Doc(
                """
                A single string with actually several scopes separated by spaces. Each
                scope is also a string.

                For example, a single string with:

                ```python
                "items:read items:write users:read profile openid"
                ````

                would represent the scopes:

                * `items:read`
                * `items:write`
                * `users:read`
                * `profile`
                * `openid`
                """
            ),
        ] = "",
        client_id: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_id`, it can be sent as part of the form fields.
                But the OAuth2 specification recommends sending the `client_id` and
                `client_secret` (if any) using HTTP Basic auth.
                """
            ),
        ] = None,
        client_secret: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_password` (and a `client_id`), they can be sent
                as part of the form fields. But the OAuth2 specification recommends
                sending the `client_id` and `client_secret` (if any) using HTTP Basic
                auth.
                """
            ),
        ] = None,
    ):
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )


class OAuth2(SecurityBase):
    """
    This is the base class for OAuth2 authentication, an instance of it would be used
    as a dependency. All other OAuth2 classes inherit from it and customize it for
    each OAuth2 flow.

    You normally would not create a new class inheriting from it but use one of the
    existing subclasses, and maybe compose them if you want to support multiple flows.

    Read more about it in the
    [FastAPI docs for Security](https://fastapi.tiangolo.com/tutorial/security/).
    """

    def __init__(
        self,
        *,
        flows: Annotated[
            Union[OAuthFlowsModel, Dict[str, Dict[str, Any]]],
            Doc(
                """
                The dictionary of OAuth2 flows.
                """
            ),
        ] = OAuthFlowsModel(),
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
                OAuth2 authentication, it will automatically cancel the request and
                send the client an error.

                If `auto_error` is set to `False`, when the HTTP Authorization header
                is not available, instead of erroring out, the dependency result will
                be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, with OAuth2
                or in a cookie).
                """
            ),
        ] = True,
    ):
        self.model = OAuth2Model(
            flows=cast(OAuthFlowsModel, flows), description=description
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


class OAuth2PasswordBearer(OAuth2):
    """
    OAuth2 flow for authentication using a bearer token obtained with a password.
    An instance of it would be used as a dependency.

    Read more about it in the
    [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
    """

    def __init__(
        self,
        tokenUrl: Annotated[
            str,
            Doc(
                """
                The URL to obtain the OAuth2 token. This would be the *path operation*
                that has `OAuth2PasswordRequestForm` as a dependency.
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
        scopes: Annotated[
            Optional[Dict[str, str]],
            Doc(
                """
                The OAuth2 scopes that would be required by the *path operations* that
                use this dependency.
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
                OAuth2 authentication, it will automatically cancel the request and
                send the client an error.

                If `auto_error` is set to `False`, when the HTTP Authorization header
                is not available, instead of erroring out, the dependency result will
                be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, with OAuth2
                or in a cookie).
                """
            ),
        ] = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password=cast(Any, {"tokenUrl": tokenUrl, "scopes": scopes})
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


class OAuth2AuthorizationCodeBearer(OAuth2):
    """
    OAuth2 flow for authentication using a bearer token obtained with an OAuth2 code
    flow. An instance of it would be used as a dependency.
    """

    def __init__(
        self,
        authorizationUrl: str,
        tokenUrl: Annotated[
            str,
            Doc(
                """
                The URL to obtain the OAuth2 token.
                """
            ),
        ],
        refreshUrl: Annotated[
            Optional[str],
            Doc(
                """
                The URL to refresh the token and obtain a new one.
                """
            ),
        ] = None,
        scheme_name: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        scopes: Annotated[
            Optional[Dict[str, str]],
            Doc(
                """
                The OAuth2 scopes that would be required by the *path operations* that
                use this dependency.
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
                OAuth2 authentication, it will automatically cancel the request and
                send the client an error.

                If `auto_error` is set to `False`, when the HTTP Authorization header
                is not available, instead of erroring out, the dependency result will
                be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, with OAuth2
                or in a cookie).
                """
            ),
        ] = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            authorizationCode=cast(
                Any,
                {
                    "authorizationUrl": authorizationUrl,
                    "tokenUrl": tokenUrl,
                    "refreshUrl": refreshUrl,
                    "scopes": scopes,
                },
            )
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None  # pragma: nocover
        return param


class SecurityScopes:
    """
    This is a special class that you can define in a parameter in a dependency to
    obtain the OAuth2 scopes required by all the dependencies in the same chain.

    This way, multiple dependencies can have different scopes, even when used in the
    same *path operation*. And with this, you can access all the scopes required in
    all those dependencies in a single place.

    Read more about it in the
    [FastAPI docs for OAuth2 scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/).
    """

    def __init__(
        self,
        scopes: Annotated[
            Optional[List[str]],
            Doc(
                """
                This will be filled by FastAPI.
                """
            ),
        ] = None,
    ):
        self.scopes: Annotated[
            List[str],
            Doc(
                """
                The list of all the scopes required by dependencies.
                """
            ),
        ] = scopes or []
        self.scope_str: Annotated[
            str,
            Doc(
                """
                All the scopes required by all the dependencies in a single string
                separated by spaces, as defined in the OAuth2 specification.
                """
            ),
        ] = " ".join(self.scopes)
