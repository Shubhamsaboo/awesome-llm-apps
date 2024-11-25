"""Validator functions for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""

from __future__ import annotations as _annotations

import math
import re
import typing
from decimal import Decimal
from fractions import Fraction
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Any, Callable, Union

from pydantic_core import PydanticCustomError, core_schema
from pydantic_core._pydantic_core import PydanticKnownError


def sequence_validator(
    input_value: typing.Sequence[Any],
    /,
    validator: core_schema.ValidatorFunctionWrapHandler,
) -> typing.Sequence[Any]:
    """Validator for `Sequence` types, isinstance(v, Sequence) has already been called."""
    value_type = type(input_value)

    # We don't accept any plain string as a sequence
    # Relevant issue: https://github.com/pydantic/pydantic/issues/5595
    if issubclass(value_type, (str, bytes)):
        raise PydanticCustomError(
            'sequence_str',
            "'{type_name}' instances are not allowed as a Sequence value",
            {'type_name': value_type.__name__},
        )

    # TODO: refactor sequence validation to validate with either a list or a tuple
    # schema, depending on the type of the value.
    # Additionally, we should be able to remove one of either this validator or the
    # SequenceValidator in _std_types_schema.py (preferably this one, while porting over some logic).
    # Effectively, a refactor for sequence validation is needed.
    if value_type is tuple:
        input_value = list(input_value)

    v_list = validator(input_value)

    # the rest of the logic is just re-creating the original type from `v_list`
    if value_type is list:
        return v_list
    elif issubclass(value_type, range):
        # return the list as we probably can't re-create the range
        return v_list
    elif value_type is tuple:
        return tuple(v_list)
    else:
        # best guess at how to re-create the original type, more custom construction logic might be required
        return value_type(v_list)  # type: ignore[call-arg]


def import_string(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return _import_string_logic(value)
        except ImportError as e:
            raise PydanticCustomError('import_error', 'Invalid python path: {error}', {'error': str(e)}) from e
    else:
        # otherwise we just return the value and let the next validator do the rest of the work
        return value


def _import_string_logic(dotted_path: str) -> Any:
    """Inspired by uvicorn — dotted paths should include a colon before the final item if that item is not a module.
    (This is necessary to distinguish between a submodule and an attribute when there is a conflict.).

    If the dotted path does not include a colon and the final item is not a valid module, importing as an attribute
    rather than a submodule will be attempted automatically.

    So, for example, the following values of `dotted_path` result in the following returned values:
    * 'collections': <module 'collections'>
    * 'collections.abc': <module 'collections.abc'>
    * 'collections.abc:Mapping': <class 'collections.abc.Mapping'>
    * `collections.abc.Mapping`: <class 'collections.abc.Mapping'> (though this is a bit slower than the previous line)

    An error will be raised under any of the following scenarios:
    * `dotted_path` contains more than one colon (e.g., 'collections:abc:Mapping')
    * the substring of `dotted_path` before the colon is not a valid module in the environment (e.g., '123:Mapping')
    * the substring of `dotted_path` after the colon is not an attribute of the module (e.g., 'collections:abc123')
    """
    from importlib import import_module

    components = dotted_path.strip().split(':')
    if len(components) > 2:
        raise ImportError(f"Import strings should have at most one ':'; received {dotted_path!r}")

    module_path = components[0]
    if not module_path:
        raise ImportError(f'Import strings should have a nonempty module name; received {dotted_path!r}')

    try:
        module = import_module(module_path)
    except ModuleNotFoundError as e:
        if '.' in module_path:
            # Check if it would be valid if the final item was separated from its module with a `:`
            maybe_module_path, maybe_attribute = dotted_path.strip().rsplit('.', 1)
            try:
                return _import_string_logic(f'{maybe_module_path}:{maybe_attribute}')
            except ImportError:
                pass
            raise ImportError(f'No module named {module_path!r}') from e
        raise e

    if len(components) > 1:
        attribute = components[1]
        try:
            return getattr(module, attribute)
        except AttributeError as e:
            raise ImportError(f'cannot import name {attribute!r} from {module_path!r}') from e
    else:
        return module


def pattern_either_validator(input_value: Any, /) -> typing.Pattern[Any]:
    if isinstance(input_value, typing.Pattern):
        return input_value
    elif isinstance(input_value, (str, bytes)):
        # todo strict mode
        return compile_pattern(input_value)  # type: ignore
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_str_validator(input_value: Any, /) -> typing.Pattern[str]:
    if isinstance(input_value, typing.Pattern):
        if isinstance(input_value.pattern, str):
            return input_value
        else:
            raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    elif isinstance(input_value, str):
        return compile_pattern(input_value)
    elif isinstance(input_value, bytes):
        raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_bytes_validator(input_value: Any, /) -> typing.Pattern[bytes]:
    if isinstance(input_value, typing.Pattern):
        if isinstance(input_value.pattern, bytes):
            return input_value
        else:
            raise PydanticCustomError('pattern_bytes_type', 'Input should be a bytes pattern')
    elif isinstance(input_value, bytes):
        return compile_pattern(input_value)
    elif isinstance(input_value, str):
        raise PydanticCustomError('pattern_bytes_type', 'Input should be a bytes pattern')
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


PatternType = typing.TypeVar('PatternType', str, bytes)


def compile_pattern(pattern: PatternType) -> typing.Pattern[PatternType]:
    try:
        return re.compile(pattern)
    except re.error:
        raise PydanticCustomError('pattern_regex', 'Input should be a valid regular expression')


def ip_v4_address_validator(input_value: Any, /) -> IPv4Address:
    if isinstance(input_value, IPv4Address):
        return input_value

    try:
        return IPv4Address(input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_address', 'Input is not a valid IPv4 address')


def ip_v6_address_validator(input_value: Any, /) -> IPv6Address:
    if isinstance(input_value, IPv6Address):
        return input_value

    try:
        return IPv6Address(input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_address', 'Input is not a valid IPv6 address')


def ip_v4_network_validator(input_value: Any, /) -> IPv4Network:
    """Assume IPv4Network initialised with a default `strict` argument.

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv4Network
    """
    if isinstance(input_value, IPv4Network):
        return input_value

    try:
        return IPv4Network(input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_network', 'Input is not a valid IPv4 network')


def ip_v6_network_validator(input_value: Any, /) -> IPv6Network:
    """Assume IPv6Network initialised with a default `strict` argument.

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv6Network
    """
    if isinstance(input_value, IPv6Network):
        return input_value

    try:
        return IPv6Network(input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_network', 'Input is not a valid IPv6 network')


def ip_v4_interface_validator(input_value: Any, /) -> IPv4Interface:
    if isinstance(input_value, IPv4Interface):
        return input_value

    try:
        return IPv4Interface(input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_interface', 'Input is not a valid IPv4 interface')


def ip_v6_interface_validator(input_value: Any, /) -> IPv6Interface:
    if isinstance(input_value, IPv6Interface):
        return input_value

    try:
        return IPv6Interface(input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_interface', 'Input is not a valid IPv6 interface')


def fraction_validator(input_value: Any, /) -> Fraction:
    if isinstance(input_value, Fraction):
        return input_value

    try:
        return Fraction(input_value)
    except ValueError:
        raise PydanticCustomError('fraction_parsing', 'Input is not a valid fraction')


def forbid_inf_nan_check(x: Any) -> Any:
    if not math.isfinite(x):
        raise PydanticKnownError('finite_number')
    return x


def _safe_repr(v: Any) -> int | float | str:
    """The context argument for `PydanticKnownError` requires a number or str type, so we do a simple repr() coercion for types like timedelta.

    See tests/test_types.py::test_annotated_metadata_any_order for some context.
    """
    if isinstance(v, (int, float, str)):
        return v
    return repr(v)


def greater_than_validator(x: Any, gt: Any) -> Any:
    try:
        if not (x > gt):
            raise PydanticKnownError('greater_than', {'gt': _safe_repr(gt)})
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'gt' to supplied value {x}")


def greater_than_or_equal_validator(x: Any, ge: Any) -> Any:
    try:
        if not (x >= ge):
            raise PydanticKnownError('greater_than_equal', {'ge': _safe_repr(ge)})
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'ge' to supplied value {x}")


def less_than_validator(x: Any, lt: Any) -> Any:
    try:
        if not (x < lt):
            raise PydanticKnownError('less_than', {'lt': _safe_repr(lt)})
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'lt' to supplied value {x}")


def less_than_or_equal_validator(x: Any, le: Any) -> Any:
    try:
        if not (x <= le):
            raise PydanticKnownError('less_than_equal', {'le': _safe_repr(le)})
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'le' to supplied value {x}")


def multiple_of_validator(x: Any, multiple_of: Any) -> Any:
    try:
        if x % multiple_of:
            raise PydanticKnownError('multiple_of', {'multiple_of': _safe_repr(multiple_of)})
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'multiple_of' to supplied value {x}")


def min_length_validator(x: Any, min_length: Any) -> Any:
    try:
        if not (len(x) >= min_length):
            raise PydanticKnownError(
                'too_short', {'field_type': 'Value', 'min_length': min_length, 'actual_length': len(x)}
            )
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'min_length' to supplied value {x}")


def max_length_validator(x: Any, max_length: Any) -> Any:
    try:
        if len(x) > max_length:
            raise PydanticKnownError(
                'too_long',
                {'field_type': 'Value', 'max_length': max_length, 'actual_length': len(x)},
            )
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'max_length' to supplied value {x}")


def _extract_decimal_digits_info(decimal: Decimal) -> tuple[int, int]:
    """Compute the total number of digits and decimal places for a given [`Decimal`][decimal.Decimal] instance.

    This function handles both normalized and non-normalized Decimal instances.
    Example: Decimal('1.230') -> 4 digits, 3 decimal places

    Args:
        decimal (Decimal): The decimal number to analyze.

    Returns:
        tuple[int, int]: A tuple containing the number of decimal places and total digits.

    Though this could be divided into two separate functions, the logic is easier to follow if we couple the computation
    of the number of decimals and digits together.
    """
    decimal_tuple = decimal.as_tuple()
    if not isinstance(decimal_tuple.exponent, int):
        raise TypeError(f'Unable to extract decimal digits info from supplied value {decimal}')
    exponent = decimal_tuple.exponent
    num_digits = len(decimal_tuple.digits)

    if exponent >= 0:
        # A positive exponent adds that many trailing zeros
        # Ex: digit_tuple=(1, 2, 3), exponent=2 -> 12300 -> 0 decimal places, 5 digits
        num_digits += exponent
        decimal_places = 0
    else:
        # If the absolute value of the negative exponent is larger than the
        # number of digits, then it's the same as the number of digits,
        # because it'll consume all the digits in digit_tuple and then
        # add abs(exponent) - len(digit_tuple) leading zeros after the decimal point.
        # Ex: digit_tuple=(1, 2, 3), exponent=-2 -> 1.23 -> 2 decimal places, 3 digits
        # Ex: digit_tuple=(1, 2, 3), exponent=-4 -> 0.0123 -> 4 decimal places, 4 digits
        decimal_places = abs(exponent)
        num_digits = max(num_digits, decimal_places)

    return decimal_places, num_digits


def max_digits_validator(x: Any, max_digits: Any) -> Any:
    _, num_digits = _extract_decimal_digits_info(x)
    _, normalized_num_digits = _extract_decimal_digits_info(x.normalize())

    try:
        if (num_digits > max_digits) and (normalized_num_digits > max_digits):
            raise PydanticKnownError(
                'decimal_max_digits',
                {'max_digits': max_digits},
            )
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'max_digits' to supplied value {x}")


def decimal_places_validator(x: Any, decimal_places: Any) -> Any:
    decimal_places_, _ = _extract_decimal_digits_info(x)
    normalized_decimal_places, _ = _extract_decimal_digits_info(x.normalize())

    try:
        if (decimal_places_ > decimal_places) and (normalized_decimal_places > decimal_places):
            raise PydanticKnownError(
                'decimal_max_places',
                {'decimal_places': decimal_places},
            )
        return x
    except TypeError:
        raise TypeError(f"Unable to apply constraint 'decimal_places' to supplied value {x}")


NUMERIC_VALIDATOR_LOOKUP: dict[str, Callable] = {
    'gt': greater_than_validator,
    'ge': greater_than_or_equal_validator,
    'lt': less_than_validator,
    'le': less_than_or_equal_validator,
    'multiple_of': multiple_of_validator,
    'min_length': min_length_validator,
    'max_length': max_length_validator,
    'max_digits': max_digits_validator,
    'decimal_places': decimal_places_validator,
}

IpType = Union[IPv4Address, IPv6Address, IPv4Network, IPv6Network, IPv4Interface, IPv6Interface]

IP_VALIDATOR_LOOKUP: dict[type[IpType], Callable] = {
    IPv4Address: ip_v4_address_validator,
    IPv6Address: ip_v6_address_validator,
    IPv4Network: ip_v4_network_validator,
    IPv6Network: ip_v6_network_validator,
    IPv4Interface: ip_v4_interface_validator,
    IPv6Interface: ip_v6_interface_validator,
}
