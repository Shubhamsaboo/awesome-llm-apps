from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager
from functools import cached_property
from typing import Any, Callable, Iterator, Mapping, NamedTuple, TypeVar

from typing_extensions import TypeAlias, TypeAliasType

GlobalsNamespace: TypeAlias = 'dict[str, Any]'
"""A global namespace.

In most cases, this is a reference to the `__dict__` attribute of a module.
This namespace type is expected as the `globals` argument during annotations evaluation.
"""

MappingNamespace: TypeAlias = Mapping[str, Any]
"""Any kind of namespace.

In most cases, this is a local namespace (e.g. the `__dict__` attribute of a class,
the [`f_locals`][frame.f_locals] attribute of a frame object, when dealing with types
defined inside functions).
This namespace type is expected as the `locals` argument during annotations evaluation.
"""


class NamespacesTuple(NamedTuple):
    """A tuple of globals and locals to be used during annotations evaluation.

    This datastructure is defined as a named tuple so that it can easily be unpacked:

    ```python {lint="skip" test="skip"}
    def eval_type(typ: type[Any], ns: NamespacesTuple) -> None:
        return eval(typ, *ns)
    ```
    """

    globals: GlobalsNamespace
    """The namespace to be used as the `globals` argument during annotations evaluation."""

    locals: MappingNamespace
    """The namespace to be used as the `locals` argument during annotations evaluation."""


def get_module_ns_of(obj: Any) -> dict[str, Any]:
    """Get the namespace of the module where the object is defined.

    Caution: this function does not return a copy of the module namespace, so the result
    should not be mutated. The burden of enforcing this is on the caller.
    """
    module_name = getattr(obj, '__module__', None)
    if module_name:
        try:
            return sys.modules[module_name].__dict__
        except KeyError:
            # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
            return {}
    return {}


# Note that this class is almost identical to `collections.ChainMap`, but need to enforce
# immutable mappings here:
class LazyLocalNamespace(Mapping[str, Any]):
    """A lazily evaluated mapping, to be used as the `locals` argument during annotations evaluation.

    While the [`eval`][eval] function expects a mapping as the `locals` argument, it only
    performs `__getitem__` calls. The [`Mapping`][collections.abc.Mapping] abstract base class
    is fully implemented only for type checking purposes.

    Args:
        *namespaces: The namespaces to consider, in ascending order of priority.

    Example:
        ```python {lint="skip" test="skip"}
        ns = LazyLocalNamespace({'a': 1, 'b': 2}, {'a': 3})
        ns['a']
        #> 3
        ns['b']
        #> 2
        ```
    """

    def __init__(self, *namespaces: MappingNamespace) -> None:
        self._namespaces = namespaces

    @cached_property
    def data(self) -> dict[str, Any]:
        return {k: v for ns in self._namespaces for k, v in ns.items()}

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: object) -> bool:
        return key in self.data

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)


def ns_for_function(obj: Callable[..., Any], parent_namespace: MappingNamespace | None = None) -> NamespacesTuple:
    """Return the global and local namespaces to be used when evaluating annotations for the provided function.

    The global namespace will be the `__dict__` attribute of the module the function was defined in.
    The local namespace will contain the `__type_params__` introduced by PEP 695.

    Args:
        obj: The object to use when building namespaces.
        parent_namespace: Optional namespace to be added with the lowest priority in the local namespace.
            If the passed function is a method, the `parent_namespace` will be the namespace of the class
            the method is defined in. Thus, we also fetch type `__type_params__` from there (i.e. the
            class-scoped type variables).
    """
    locals_list: list[MappingNamespace] = []
    if parent_namespace is not None:
        locals_list.append(parent_namespace)

    # Get the `__type_params__` attribute introduced by PEP 695.
    # Note that the `typing._eval_type` function expects type params to be
    # passed as a separate argument. However, internally, `_eval_type` calls
    # `ForwardRef._evaluate` which will merge type params with the localns,
    # essentially mimicking what we do here.
    type_params: tuple[TypeVar, ...] = ()
    if parent_namespace is not None:
        # We also fetch type params from the parent namespace. If present, it probably
        # means the function was defined in a class. This is to support the following:
        # https://github.com/python/cpython/issues/124089.
        type_params += parent_namespace.get('__type_params__', ())

    locals_list.append({t.__name__: t for t in type_params})

    # What about short-cirtuiting to `obj.__globals__`?
    globalns = get_module_ns_of(obj)

    return NamespacesTuple(globalns, LazyLocalNamespace(*locals_list))


class NsResolver:
    """A class responsible for the namespaces resolving logic for annotations evaluation.

    This class handles the namespace logic when evaluating annotations mainly for class objects.

    It holds a stack of classes that are being inspected during the core schema building,
    and the `types_namespace` property exposes the globals and locals to be used for
    type annotation evaluation. Additionally -- if no class is present in the stack -- a
    fallback globals and locals can be provided using the `namespaces_tuple` argument
    (this is useful when generating a schema for a simple annotation, e.g. when using
    `TypeAdapter`).

    The namespace creation logic is unfortunately flawed in some cases, for backwards
    compatibility reasons and to better support valid edge cases. See the description
    for the `parent_namespace` argument and the example for more details.

    Args:
        namespaces_tuple: The default globals and locals to use if no class is present
            on the stack. This can be useful when using the `GenerateSchema` class
            with `TypeAdapter`, where the "type" being analyzed is a simple annotation.
        parent_namespace: An optional parent namespace that will be added to the locals
            with the lowest priority. For a given class defined in a function, the locals
            of this function are usually used as the parent namespace:

            ```python {lint="skip" test="skip"}
            from pydantic import BaseModel

            def func() -> None:
                SomeType = int

                class Model(BaseModel):
                    f: 'SomeType'

                # when collecting fields, an namespace resolver instance will be created
                # this way:
                # ns_resolver = NsResolver(parent_namespace={'SomeType': SomeType})
            ```

            For backwards compatibility reasons and to support valid edge cases, this parent
            namespace will be used for *every* type being pushed to the stack. In the future,
            we might want to be smarter by only doing so when the type being pushed is defined
            in the same module as the parent namespace.

    Example:
        ```python {lint="skip" test="skip"}
        ns_resolver = NsResolver(
            parent_namespace={'fallback': 1},
        )

        class Sub:
            m: 'Model'

        class Model:
            some_local = 1
            sub: Sub

        ns_resolver = NsResolver()

        # This is roughly what happens when we build a core schema for `Model`:
        with ns_resolver.push(Model):
            ns_resolver.types_namespace
            #> NamespacesTuple({'Sub': Sub}, {'Model': Model, 'some_local': 1})
            # First thing to notice here, the model being pushed is added to the locals.
            # Because `NsResolver` is being used during the model definition, it is not
            # yet added to the globals. This is useful when resolving self-referencing annotations.

            with ns_resolver.push(Sub):
                ns_resolver.types_namespace
                #> NamespacesTuple({'Sub': Sub}, {'Sub': Sub, 'Model': Model})
                # Second thing to notice: `Sub` is present in both the globals and locals.
                # This is not an issue, just that as described above, the model being pushed
                # is added to the locals, but it happens to be present in the globals as well
                # because it is already defined.
                # Third thing to notice: `Model` is also added in locals. This is a backwards
                # compatibility workaround that allows for `Sub` to be able to resolve `'Model'`
                # correctly (as otherwise models would have to be rebuilt even though this
                # doesn't look necessary).
        ```
    """

    def __init__(
        self,
        namespaces_tuple: NamespacesTuple | None = None,
        parent_namespace: MappingNamespace | None = None,
    ) -> None:
        self._base_ns_tuple = namespaces_tuple or NamespacesTuple({}, {})
        self._parent_ns = parent_namespace
        self._types_stack: list[type[Any] | TypeAliasType] = []

    @cached_property
    def types_namespace(self) -> NamespacesTuple:
        """The current global and local namespaces to be used for annotations evaluation."""
        if not self._types_stack:
            # TODO: should we merge the parent namespace here?
            # This is relevant for TypeAdapter, where there are no types on the stack, and we might
            # need access to the parent_ns. Right now, we sidestep this in `type_adapter.py` by passing
            # locals to both parent_ns and the base_ns_tuple, but this is a bit hacky.
            # we might consider something like:
            # if self._parent_ns is not None:
            #     # Hacky workarounds, see class docstring:
            #     # An optional parent namespace that will be added to the locals with the lowest priority
            #     locals_list: list[MappingNamespace] = [self._parent_ns, self._base_ns_tuple.locals]
            #     return NamespacesTuple(self._base_ns_tuple.globals, LazyLocalNamespace(*locals_list))
            return self._base_ns_tuple

        typ = self._types_stack[-1]

        globalns = get_module_ns_of(typ)

        locals_list: list[MappingNamespace] = []
        # Hacky workarounds, see class docstring:
        # An optional parent namespace that will be added to the locals with the lowest priority
        if self._parent_ns is not None:
            locals_list.append(self._parent_ns)
        if len(self._types_stack) > 1:
            first_type = self._types_stack[0]
            locals_list.append({first_type.__name__: first_type})

        if hasattr(typ, '__dict__'):
            # TypeAliasType is the exception.
            locals_list.append(vars(typ))

        # The len check above presents this from being added twice:
        locals_list.append({typ.__name__: typ})

        return NamespacesTuple(globalns, LazyLocalNamespace(*locals_list))

    @contextmanager
    def push(self, typ: type[Any] | TypeAliasType, /) -> Generator[None]:
        """Push a type to the stack."""
        self._types_stack.append(typ)
        # Reset the cached property:
        self.__dict__.pop('types_namespace', None)
        try:
            yield
        finally:
            self._types_stack.pop()
            self.__dict__.pop('types_namespace', None)
