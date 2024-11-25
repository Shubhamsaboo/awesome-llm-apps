import inspect
from contextlib import AsyncExitStack, contextmanager
from copy import copy, deepcopy
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    ForwardRef,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import anyio
from fastapi import params
from fastapi._compat import (
    PYDANTIC_V2,
    ErrorWrapper,
    ModelField,
    RequiredParam,
    Undefined,
    _regenerate_error_with_loc,
    copy_field_info,
    create_body_model,
    evaluate_forwardref,
    field_annotation_is_scalar,
    get_annotation_from_field_info,
    get_cached_model_fields,
    get_missing_field_error,
    is_bytes_field,
    is_bytes_sequence_field,
    is_scalar_field,
    is_scalar_sequence_field,
    is_sequence_field,
    is_uploadfile_or_nonable_uploadfile_annotation,
    is_uploadfile_sequence_annotation,
    lenient_issubclass,
    sequence_types,
    serialize_sequence_value,
    value_is_sequence,
)
from fastapi.background import BackgroundTasks
from fastapi.concurrency import (
    asynccontextmanager,
    contextmanager_in_threadpool,
)
from fastapi.dependencies.models import Dependant, SecurityRequirement
from fastapi.logger import logger
from fastapi.security.base import SecurityBase
from fastapi.security.oauth2 import OAuth2, SecurityScopes
from fastapi.security.open_id_connect_url import OpenIdConnect
from fastapi.utils import create_model_field, get_path_param_names
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from starlette.background import BackgroundTasks as StarletteBackgroundTasks
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import (
    FormData,
    Headers,
    ImmutableMultiDict,
    QueryParams,
    UploadFile,
)
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.websockets import WebSocket
from typing_extensions import Annotated, get_args, get_origin

multipart_not_installed_error = (
    'Form data requires "python-multipart" to be installed. \n'
    'You can install "python-multipart" with: \n\n'
    "pip install python-multipart\n"
)
multipart_incorrect_install_error = (
    'Form data requires "python-multipart" to be installed. '
    'It seems you installed "multipart" instead. \n'
    'You can remove "multipart" with: \n\n'
    "pip uninstall multipart\n\n"
    'And then install "python-multipart" with: \n\n'
    "pip install python-multipart\n"
)


def ensure_multipart_is_installed() -> None:
    try:
        from python_multipart import __version__

        # Import an attribute that can be mocked/deleted in testing
        assert __version__ > "0.0.12"
    except (ImportError, AssertionError):
        try:
            # __version__ is available in both multiparts, and can be mocked
            from multipart import __version__  # type: ignore[no-redef,import-untyped]

            assert __version__
            try:
                # parse_options_header is only available in the right multipart
                from multipart.multipart import (  # type: ignore[import-untyped]
                    parse_options_header,
                )

                assert parse_options_header
            except ImportError:
                logger.error(multipart_incorrect_install_error)
                raise RuntimeError(multipart_incorrect_install_error) from None
        except ImportError:
            logger.error(multipart_not_installed_error)
            raise RuntimeError(multipart_not_installed_error) from None


def get_param_sub_dependant(
    *,
    param_name: str,
    depends: params.Depends,
    path: str,
    security_scopes: Optional[List[str]] = None,
) -> Dependant:
    assert depends.dependency
    return get_sub_dependant(
        depends=depends,
        dependency=depends.dependency,
        path=path,
        name=param_name,
        security_scopes=security_scopes,
    )


def get_parameterless_sub_dependant(*, depends: params.Depends, path: str) -> Dependant:
    assert callable(
        depends.dependency
    ), "A parameter-less dependency must have a callable dependency"
    return get_sub_dependant(depends=depends, dependency=depends.dependency, path=path)


def get_sub_dependant(
    *,
    depends: params.Depends,
    dependency: Callable[..., Any],
    path: str,
    name: Optional[str] = None,
    security_scopes: Optional[List[str]] = None,
) -> Dependant:
    security_requirement = None
    security_scopes = security_scopes or []
    if isinstance(depends, params.Security):
        dependency_scopes = depends.scopes
        security_scopes.extend(dependency_scopes)
    if isinstance(dependency, SecurityBase):
        use_scopes: List[str] = []
        if isinstance(dependency, (OAuth2, OpenIdConnect)):
            use_scopes = security_scopes
        security_requirement = SecurityRequirement(
            security_scheme=dependency, scopes=use_scopes
        )
    sub_dependant = get_dependant(
        path=path,
        call=dependency,
        name=name,
        security_scopes=security_scopes,
        use_cache=depends.use_cache,
    )
    if security_requirement:
        sub_dependant.security_requirements.append(security_requirement)
    return sub_dependant


CacheKey = Tuple[Optional[Callable[..., Any]], Tuple[str, ...]]


def get_flat_dependant(
    dependant: Dependant,
    *,
    skip_repeats: bool = False,
    visited: Optional[List[CacheKey]] = None,
) -> Dependant:
    if visited is None:
        visited = []
    visited.append(dependant.cache_key)

    flat_dependant = Dependant(
        path_params=dependant.path_params.copy(),
        query_params=dependant.query_params.copy(),
        header_params=dependant.header_params.copy(),
        cookie_params=dependant.cookie_params.copy(),
        body_params=dependant.body_params.copy(),
        security_requirements=dependant.security_requirements.copy(),
        use_cache=dependant.use_cache,
        path=dependant.path,
    )
    for sub_dependant in dependant.dependencies:
        if skip_repeats and sub_dependant.cache_key in visited:
            continue
        flat_sub = get_flat_dependant(
            sub_dependant, skip_repeats=skip_repeats, visited=visited
        )
        flat_dependant.path_params.extend(flat_sub.path_params)
        flat_dependant.query_params.extend(flat_sub.query_params)
        flat_dependant.header_params.extend(flat_sub.header_params)
        flat_dependant.cookie_params.extend(flat_sub.cookie_params)
        flat_dependant.body_params.extend(flat_sub.body_params)
        flat_dependant.security_requirements.extend(flat_sub.security_requirements)
    return flat_dependant


def _get_flat_fields_from_params(fields: List[ModelField]) -> List[ModelField]:
    if not fields:
        return fields
    first_field = fields[0]
    if len(fields) == 1 and lenient_issubclass(first_field.type_, BaseModel):
        fields_to_extract = get_cached_model_fields(first_field.type_)
        return fields_to_extract
    return fields


def get_flat_params(dependant: Dependant) -> List[ModelField]:
    flat_dependant = get_flat_dependant(dependant, skip_repeats=True)
    path_params = _get_flat_fields_from_params(flat_dependant.path_params)
    query_params = _get_flat_fields_from_params(flat_dependant.query_params)
    header_params = _get_flat_fields_from_params(flat_dependant.header_params)
    cookie_params = _get_flat_fields_from_params(flat_dependant.cookie_params)
    return path_params + query_params + header_params + cookie_params


def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    signature = inspect.signature(call)
    globalns = getattr(call, "__globals__", {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=get_typed_annotation(param.annotation, globalns),
        )
        for param in signature.parameters.values()
    ]
    typed_signature = inspect.Signature(typed_params)
    return typed_signature


def get_typed_annotation(annotation: Any, globalns: Dict[str, Any]) -> Any:
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return annotation


def get_typed_return_annotation(call: Callable[..., Any]) -> Any:
    signature = inspect.signature(call)
    annotation = signature.return_annotation

    if annotation is inspect.Signature.empty:
        return None

    globalns = getattr(call, "__globals__", {})
    return get_typed_annotation(annotation, globalns)


def get_dependant(
    *,
    path: str,
    call: Callable[..., Any],
    name: Optional[str] = None,
    security_scopes: Optional[List[str]] = None,
    use_cache: bool = True,
) -> Dependant:
    path_param_names = get_path_param_names(path)
    endpoint_signature = get_typed_signature(call)
    signature_params = endpoint_signature.parameters
    dependant = Dependant(
        call=call,
        name=name,
        path=path,
        security_scopes=security_scopes,
        use_cache=use_cache,
    )
    for param_name, param in signature_params.items():
        is_path_param = param_name in path_param_names
        param_details = analyze_param(
            param_name=param_name,
            annotation=param.annotation,
            value=param.default,
            is_path_param=is_path_param,
        )
        if param_details.depends is not None:
            sub_dependant = get_param_sub_dependant(
                param_name=param_name,
                depends=param_details.depends,
                path=path,
                security_scopes=security_scopes,
            )
            dependant.dependencies.append(sub_dependant)
            continue
        if add_non_field_param_to_dependency(
            param_name=param_name,
            type_annotation=param_details.type_annotation,
            dependant=dependant,
        ):
            assert (
                param_details.field is None
            ), f"Cannot specify multiple FastAPI annotations for {param_name!r}"
            continue
        assert param_details.field is not None
        if isinstance(param_details.field.field_info, params.Body):
            dependant.body_params.append(param_details.field)
        else:
            add_param_to_fields(field=param_details.field, dependant=dependant)
    return dependant


def add_non_field_param_to_dependency(
    *, param_name: str, type_annotation: Any, dependant: Dependant
) -> Optional[bool]:
    if lenient_issubclass(type_annotation, Request):
        dependant.request_param_name = param_name
        return True
    elif lenient_issubclass(type_annotation, WebSocket):
        dependant.websocket_param_name = param_name
        return True
    elif lenient_issubclass(type_annotation, HTTPConnection):
        dependant.http_connection_param_name = param_name
        return True
    elif lenient_issubclass(type_annotation, Response):
        dependant.response_param_name = param_name
        return True
    elif lenient_issubclass(type_annotation, StarletteBackgroundTasks):
        dependant.background_tasks_param_name = param_name
        return True
    elif lenient_issubclass(type_annotation, SecurityScopes):
        dependant.security_scopes_param_name = param_name
        return True
    return None


@dataclass
class ParamDetails:
    type_annotation: Any
    depends: Optional[params.Depends]
    field: Optional[ModelField]


def analyze_param(
    *,
    param_name: str,
    annotation: Any,
    value: Any,
    is_path_param: bool,
) -> ParamDetails:
    field_info = None
    depends = None
    type_annotation: Any = Any
    use_annotation: Any = Any
    if annotation is not inspect.Signature.empty:
        use_annotation = annotation
        type_annotation = annotation
    # Extract Annotated info
    if get_origin(use_annotation) is Annotated:
        annotated_args = get_args(annotation)
        type_annotation = annotated_args[0]
        fastapi_annotations = [
            arg
            for arg in annotated_args[1:]
            if isinstance(arg, (FieldInfo, params.Depends))
        ]
        fastapi_specific_annotations = [
            arg
            for arg in fastapi_annotations
            if isinstance(arg, (params.Param, params.Body, params.Depends))
        ]
        if fastapi_specific_annotations:
            fastapi_annotation: Union[FieldInfo, params.Depends, None] = (
                fastapi_specific_annotations[-1]
            )
        else:
            fastapi_annotation = None
        # Set default for Annotated FieldInfo
        if isinstance(fastapi_annotation, FieldInfo):
            # Copy `field_info` because we mutate `field_info.default` below.
            field_info = copy_field_info(
                field_info=fastapi_annotation, annotation=use_annotation
            )
            assert (
                field_info.default is Undefined or field_info.default is RequiredParam
            ), (
                f"`{field_info.__class__.__name__}` default value cannot be set in"
                f" `Annotated` for {param_name!r}. Set the default value with `=` instead."
            )
            if value is not inspect.Signature.empty:
                assert not is_path_param, "Path parameters cannot have default values"
                field_info.default = value
            else:
                field_info.default = RequiredParam
        # Get Annotated Depends
        elif isinstance(fastapi_annotation, params.Depends):
            depends = fastapi_annotation
    # Get Depends from default value
    if isinstance(value, params.Depends):
        assert depends is None, (
            "Cannot specify `Depends` in `Annotated` and default value"
            f" together for {param_name!r}"
        )
        assert field_info is None, (
            "Cannot specify a FastAPI annotation in `Annotated` and `Depends` as a"
            f" default value together for {param_name!r}"
        )
        depends = value
    # Get FieldInfo from default value
    elif isinstance(value, FieldInfo):
        assert field_info is None, (
            "Cannot specify FastAPI annotations in `Annotated` and default value"
            f" together for {param_name!r}"
        )
        field_info = value
        if PYDANTIC_V2:
            field_info.annotation = type_annotation

    # Get Depends from type annotation
    if depends is not None and depends.dependency is None:
        # Copy `depends` before mutating it
        depends = copy(depends)
        depends.dependency = type_annotation

    # Handle non-param type annotations like Request
    if lenient_issubclass(
        type_annotation,
        (
            Request,
            WebSocket,
            HTTPConnection,
            Response,
            StarletteBackgroundTasks,
            SecurityScopes,
        ),
    ):
        assert depends is None, f"Cannot specify `Depends` for type {type_annotation!r}"
        assert (
            field_info is None
        ), f"Cannot specify FastAPI annotation for type {type_annotation!r}"
    # Handle default assignations, neither field_info nor depends was not found in Annotated nor default value
    elif field_info is None and depends is None:
        default_value = value if value is not inspect.Signature.empty else RequiredParam
        if is_path_param:
            # We might check here that `default_value is RequiredParam`, but the fact is that the same
            # parameter might sometimes be a path parameter and sometimes not. See
            # `tests/test_infer_param_optionality.py` for an example.
            field_info = params.Path(annotation=use_annotation)
        elif is_uploadfile_or_nonable_uploadfile_annotation(
            type_annotation
        ) or is_uploadfile_sequence_annotation(type_annotation):
            field_info = params.File(annotation=use_annotation, default=default_value)
        elif not field_annotation_is_scalar(annotation=type_annotation):
            field_info = params.Body(annotation=use_annotation, default=default_value)
        else:
            field_info = params.Query(annotation=use_annotation, default=default_value)

    field = None
    # It's a field_info, not a dependency
    if field_info is not None:
        # Handle field_info.in_
        if is_path_param:
            assert isinstance(field_info, params.Path), (
                f"Cannot use `{field_info.__class__.__name__}` for path param"
                f" {param_name!r}"
            )
        elif (
            isinstance(field_info, params.Param)
            and getattr(field_info, "in_", None) is None
        ):
            field_info.in_ = params.ParamTypes.query
        use_annotation_from_field_info = get_annotation_from_field_info(
            use_annotation,
            field_info,
            param_name,
        )
        if isinstance(field_info, params.Form):
            ensure_multipart_is_installed()
        if not field_info.alias and getattr(field_info, "convert_underscores", None):
            alias = param_name.replace("_", "-")
        else:
            alias = field_info.alias or param_name
        field_info.alias = alias
        field = create_model_field(
            name=param_name,
            type_=use_annotation_from_field_info,
            default=field_info.default,
            alias=alias,
            required=field_info.default in (RequiredParam, Undefined),
            field_info=field_info,
        )
        if is_path_param:
            assert is_scalar_field(
                field=field
            ), "Path params must be of one of the supported types"
        elif isinstance(field_info, params.Query):
            assert (
                is_scalar_field(field)
                or is_scalar_sequence_field(field)
                or (
                    lenient_issubclass(field.type_, BaseModel)
                    # For Pydantic v1
                    and getattr(field, "shape", 1) == 1
                )
            )

    return ParamDetails(type_annotation=type_annotation, depends=depends, field=field)


def add_param_to_fields(*, field: ModelField, dependant: Dependant) -> None:
    field_info = field.field_info
    field_info_in = getattr(field_info, "in_", None)
    if field_info_in == params.ParamTypes.path:
        dependant.path_params.append(field)
    elif field_info_in == params.ParamTypes.query:
        dependant.query_params.append(field)
    elif field_info_in == params.ParamTypes.header:
        dependant.header_params.append(field)
    else:
        assert (
            field_info_in == params.ParamTypes.cookie
        ), f"non-body parameters must be in path, query, header or cookie: {field.name}"
        dependant.cookie_params.append(field)


def is_coroutine_callable(call: Callable[..., Any]) -> bool:
    if inspect.isroutine(call):
        return inspect.iscoroutinefunction(call)
    if inspect.isclass(call):
        return False
    dunder_call = getattr(call, "__call__", None)  # noqa: B004
    return inspect.iscoroutinefunction(dunder_call)


def is_async_gen_callable(call: Callable[..., Any]) -> bool:
    if inspect.isasyncgenfunction(call):
        return True
    dunder_call = getattr(call, "__call__", None)  # noqa: B004
    return inspect.isasyncgenfunction(dunder_call)


def is_gen_callable(call: Callable[..., Any]) -> bool:
    if inspect.isgeneratorfunction(call):
        return True
    dunder_call = getattr(call, "__call__", None)  # noqa: B004
    return inspect.isgeneratorfunction(dunder_call)


async def solve_generator(
    *, call: Callable[..., Any], stack: AsyncExitStack, sub_values: Dict[str, Any]
) -> Any:
    if is_gen_callable(call):
        cm = contextmanager_in_threadpool(contextmanager(call)(**sub_values))
    elif is_async_gen_callable(call):
        cm = asynccontextmanager(call)(**sub_values)
    return await stack.enter_async_context(cm)


@dataclass
class SolvedDependency:
    values: Dict[str, Any]
    errors: List[Any]
    background_tasks: Optional[StarletteBackgroundTasks]
    response: Response
    dependency_cache: Dict[Tuple[Callable[..., Any], Tuple[str]], Any]


async def solve_dependencies(
    *,
    request: Union[Request, WebSocket],
    dependant: Dependant,
    body: Optional[Union[Dict[str, Any], FormData]] = None,
    background_tasks: Optional[StarletteBackgroundTasks] = None,
    response: Optional[Response] = None,
    dependency_overrides_provider: Optional[Any] = None,
    dependency_cache: Optional[Dict[Tuple[Callable[..., Any], Tuple[str]], Any]] = None,
    async_exit_stack: AsyncExitStack,
    embed_body_fields: bool,
) -> SolvedDependency:
    values: Dict[str, Any] = {}
    errors: List[Any] = []
    if response is None:
        response = Response()
        del response.headers["content-length"]
        response.status_code = None  # type: ignore
    dependency_cache = dependency_cache or {}
    sub_dependant: Dependant
    for sub_dependant in dependant.dependencies:
        sub_dependant.call = cast(Callable[..., Any], sub_dependant.call)
        sub_dependant.cache_key = cast(
            Tuple[Callable[..., Any], Tuple[str]], sub_dependant.cache_key
        )
        call = sub_dependant.call
        use_sub_dependant = sub_dependant
        if (
            dependency_overrides_provider
            and dependency_overrides_provider.dependency_overrides
        ):
            original_call = sub_dependant.call
            call = getattr(
                dependency_overrides_provider, "dependency_overrides", {}
            ).get(original_call, original_call)
            use_path: str = sub_dependant.path  # type: ignore
            use_sub_dependant = get_dependant(
                path=use_path,
                call=call,
                name=sub_dependant.name,
                security_scopes=sub_dependant.security_scopes,
            )

        solved_result = await solve_dependencies(
            request=request,
            dependant=use_sub_dependant,
            body=body,
            background_tasks=background_tasks,
            response=response,
            dependency_overrides_provider=dependency_overrides_provider,
            dependency_cache=dependency_cache,
            async_exit_stack=async_exit_stack,
            embed_body_fields=embed_body_fields,
        )
        background_tasks = solved_result.background_tasks
        dependency_cache.update(solved_result.dependency_cache)
        if solved_result.errors:
            errors.extend(solved_result.errors)
            continue
        if sub_dependant.use_cache and sub_dependant.cache_key in dependency_cache:
            solved = dependency_cache[sub_dependant.cache_key]
        elif is_gen_callable(call) or is_async_gen_callable(call):
            solved = await solve_generator(
                call=call, stack=async_exit_stack, sub_values=solved_result.values
            )
        elif is_coroutine_callable(call):
            solved = await call(**solved_result.values)
        else:
            solved = await run_in_threadpool(call, **solved_result.values)
        if sub_dependant.name is not None:
            values[sub_dependant.name] = solved
        if sub_dependant.cache_key not in dependency_cache:
            dependency_cache[sub_dependant.cache_key] = solved
    path_values, path_errors = request_params_to_args(
        dependant.path_params, request.path_params
    )
    query_values, query_errors = request_params_to_args(
        dependant.query_params, request.query_params
    )
    header_values, header_errors = request_params_to_args(
        dependant.header_params, request.headers
    )
    cookie_values, cookie_errors = request_params_to_args(
        dependant.cookie_params, request.cookies
    )
    values.update(path_values)
    values.update(query_values)
    values.update(header_values)
    values.update(cookie_values)
    errors += path_errors + query_errors + header_errors + cookie_errors
    if dependant.body_params:
        (
            body_values,
            body_errors,
        ) = await request_body_to_args(  # body_params checked above
            body_fields=dependant.body_params,
            received_body=body,
            embed_body_fields=embed_body_fields,
        )
        values.update(body_values)
        errors.extend(body_errors)
    if dependant.http_connection_param_name:
        values[dependant.http_connection_param_name] = request
    if dependant.request_param_name and isinstance(request, Request):
        values[dependant.request_param_name] = request
    elif dependant.websocket_param_name and isinstance(request, WebSocket):
        values[dependant.websocket_param_name] = request
    if dependant.background_tasks_param_name:
        if background_tasks is None:
            background_tasks = BackgroundTasks()
        values[dependant.background_tasks_param_name] = background_tasks
    if dependant.response_param_name:
        values[dependant.response_param_name] = response
    if dependant.security_scopes_param_name:
        values[dependant.security_scopes_param_name] = SecurityScopes(
            scopes=dependant.security_scopes
        )
    return SolvedDependency(
        values=values,
        errors=errors,
        background_tasks=background_tasks,
        response=response,
        dependency_cache=dependency_cache,
    )


def _validate_value_with_model_field(
    *, field: ModelField, value: Any, values: Dict[str, Any], loc: Tuple[str, ...]
) -> Tuple[Any, List[Any]]:
    if value is None:
        if field.required:
            return None, [get_missing_field_error(loc=loc)]
        else:
            return deepcopy(field.default), []
    v_, errors_ = field.validate(value, values, loc=loc)
    if isinstance(errors_, ErrorWrapper):
        return None, [errors_]
    elif isinstance(errors_, list):
        new_errors = _regenerate_error_with_loc(errors=errors_, loc_prefix=())
        return None, new_errors
    else:
        return v_, []


def _get_multidict_value(
    field: ModelField, values: Mapping[str, Any], alias: Union[str, None] = None
) -> Any:
    alias = alias or field.alias
    if is_sequence_field(field) and isinstance(values, (ImmutableMultiDict, Headers)):
        value = values.getlist(alias)
    else:
        value = values.get(alias, None)
    if (
        value is None
        or (
            isinstance(field.field_info, params.Form)
            and isinstance(value, str)  # For type checks
            and value == ""
        )
        or (is_sequence_field(field) and len(value) == 0)
    ):
        if field.required:
            return
        else:
            return deepcopy(field.default)
    return value


def request_params_to_args(
    fields: Sequence[ModelField],
    received_params: Union[Mapping[str, Any], QueryParams, Headers],
) -> Tuple[Dict[str, Any], List[Any]]:
    values: Dict[str, Any] = {}
    errors: List[Dict[str, Any]] = []

    if not fields:
        return values, errors

    first_field = fields[0]
    fields_to_extract = fields
    single_not_embedded_field = False
    if len(fields) == 1 and lenient_issubclass(first_field.type_, BaseModel):
        fields_to_extract = get_cached_model_fields(first_field.type_)
        single_not_embedded_field = True

    params_to_process: Dict[str, Any] = {}

    processed_keys = set()

    for field in fields_to_extract:
        alias = None
        if isinstance(received_params, Headers):
            # Handle fields extracted from a Pydantic Model for a header, each field
            # doesn't have a FieldInfo of type Header with the default convert_underscores=True
            convert_underscores = getattr(field.field_info, "convert_underscores", True)
            if convert_underscores:
                alias = (
                    field.alias
                    if field.alias != field.name
                    else field.name.replace("_", "-")
                )
        value = _get_multidict_value(field, received_params, alias=alias)
        if value is not None:
            params_to_process[field.name] = value
        processed_keys.add(alias or field.alias)
        processed_keys.add(field.name)

    for key, value in received_params.items():
        if key not in processed_keys:
            params_to_process[key] = value

    if single_not_embedded_field:
        field_info = first_field.field_info
        assert isinstance(
            field_info, params.Param
        ), "Params must be subclasses of Param"
        loc: Tuple[str, ...] = (field_info.in_.value,)
        v_, errors_ = _validate_value_with_model_field(
            field=first_field, value=params_to_process, values=values, loc=loc
        )
        return {first_field.name: v_}, errors_

    for field in fields:
        value = _get_multidict_value(field, received_params)
        field_info = field.field_info
        assert isinstance(
            field_info, params.Param
        ), "Params must be subclasses of Param"
        loc = (field_info.in_.value, field.alias)
        v_, errors_ = _validate_value_with_model_field(
            field=field, value=value, values=values, loc=loc
        )
        if errors_:
            errors.extend(errors_)
        else:
            values[field.name] = v_
    return values, errors


def _should_embed_body_fields(fields: List[ModelField]) -> bool:
    if not fields:
        return False
    # More than one dependency could have the same field, it would show up as multiple
    # fields but it's the same one, so count them by name
    body_param_names_set = {field.name for field in fields}
    # A top level field has to be a single field, not multiple
    if len(body_param_names_set) > 1:
        return True
    first_field = fields[0]
    # If it explicitly specifies it is embedded, it has to be embedded
    if getattr(first_field.field_info, "embed", None):
        return True
    # If it's a Form (or File) field, it has to be a BaseModel to be top level
    # otherwise it has to be embedded, so that the key value pair can be extracted
    if isinstance(first_field.field_info, params.Form) and not lenient_issubclass(
        first_field.type_, BaseModel
    ):
        return True
    return False


async def _extract_form_body(
    body_fields: List[ModelField],
    received_body: FormData,
) -> Dict[str, Any]:
    values = {}
    first_field = body_fields[0]
    first_field_info = first_field.field_info

    for field in body_fields:
        value = _get_multidict_value(field, received_body)
        if (
            isinstance(first_field_info, params.File)
            and is_bytes_field(field)
            and isinstance(value, UploadFile)
        ):
            value = await value.read()
        elif (
            is_bytes_sequence_field(field)
            and isinstance(first_field_info, params.File)
            and value_is_sequence(value)
        ):
            # For types
            assert isinstance(value, sequence_types)  # type: ignore[arg-type]
            results: List[Union[bytes, str]] = []

            async def process_fn(
                fn: Callable[[], Coroutine[Any, Any, Any]],
            ) -> None:
                result = await fn()
                results.append(result)  # noqa: B023

            async with anyio.create_task_group() as tg:
                for sub_value in value:
                    tg.start_soon(process_fn, sub_value.read)
            value = serialize_sequence_value(field=field, value=results)
        if value is not None:
            values[field.alias] = value
    for key, value in received_body.items():
        if key not in values:
            values[key] = value
    return values


async def request_body_to_args(
    body_fields: List[ModelField],
    received_body: Optional[Union[Dict[str, Any], FormData]],
    embed_body_fields: bool,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    values: Dict[str, Any] = {}
    errors: List[Dict[str, Any]] = []
    assert body_fields, "request_body_to_args() should be called with fields"
    single_not_embedded_field = len(body_fields) == 1 and not embed_body_fields
    first_field = body_fields[0]
    body_to_process = received_body

    fields_to_extract: List[ModelField] = body_fields

    if single_not_embedded_field and lenient_issubclass(first_field.type_, BaseModel):
        fields_to_extract = get_cached_model_fields(first_field.type_)

    if isinstance(received_body, FormData):
        body_to_process = await _extract_form_body(fields_to_extract, received_body)

    if single_not_embedded_field:
        loc: Tuple[str, ...] = ("body",)
        v_, errors_ = _validate_value_with_model_field(
            field=first_field, value=body_to_process, values=values, loc=loc
        )
        return {first_field.name: v_}, errors_
    for field in body_fields:
        loc = ("body", field.alias)
        value: Optional[Any] = None
        if body_to_process is not None:
            try:
                value = body_to_process.get(field.alias)
            # If the received body is a list, not a dict
            except AttributeError:
                errors.append(get_missing_field_error(loc))
                continue
        v_, errors_ = _validate_value_with_model_field(
            field=field, value=value, values=values, loc=loc
        )
        if errors_:
            errors.extend(errors_)
        else:
            values[field.name] = v_
    return values, errors


def get_body_field(
    *, flat_dependant: Dependant, name: str, embed_body_fields: bool
) -> Optional[ModelField]:
    """
    Get a ModelField representing the request body for a path operation, combining
    all body parameters into a single field if necessary.

    Used to check if it's form data (with `isinstance(body_field, params.Form)`)
    or JSON and to generate the JSON Schema for a request body.

    This is **not** used to validate/parse the request body, that's done with each
    individual body parameter.
    """
    if not flat_dependant.body_params:
        return None
    first_param = flat_dependant.body_params[0]
    if not embed_body_fields:
        return first_param
    model_name = "Body_" + name
    BodyModel = create_body_model(
        fields=flat_dependant.body_params, model_name=model_name
    )
    required = any(True for f in flat_dependant.body_params if f.required)
    BodyFieldInfo_kwargs: Dict[str, Any] = {
        "annotation": BodyModel,
        "alias": "body",
    }
    if not required:
        BodyFieldInfo_kwargs["default"] = None
    if any(isinstance(f.field_info, params.File) for f in flat_dependant.body_params):
        BodyFieldInfo: Type[params.Body] = params.File
    elif any(isinstance(f.field_info, params.Form) for f in flat_dependant.body_params):
        BodyFieldInfo = params.Form
    else:
        BodyFieldInfo = params.Body

        body_param_media_types = [
            f.field_info.media_type
            for f in flat_dependant.body_params
            if isinstance(f.field_info, params.Body)
        ]
        if len(set(body_param_media_types)) == 1:
            BodyFieldInfo_kwargs["media_type"] = body_param_media_types[0]
    final_field = create_model_field(
        name="body",
        type_=BodyModel,
        required=required,
        alias="body",
        field_info=BodyFieldInfo(**BodyFieldInfo_kwargs),
    )
    return final_field
