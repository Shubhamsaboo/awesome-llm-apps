import math
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Iterable, Iterator, List, NamedTuple, Set, Tuple

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import annotated_types as at


class Case(NamedTuple):
    """
    A test case for `annotated_types`.
    """

    annotation: Any
    valid_cases: Iterable[Any]
    invalid_cases: Iterable[Any]


def cases() -> Iterable[Case]:
    # Gt, Ge, Lt, Le
    yield Case(Annotated[int, at.Gt(4)], (5, 6, 1000), (4, 0, -1))
    yield Case(Annotated[float, at.Gt(0.5)], (0.6, 0.7, 0.8, 0.9), (0.5, 0.0, -0.1))
    yield Case(
        Annotated[datetime, at.Gt(datetime(2000, 1, 1))],
        [datetime(2000, 1, 2), datetime(2000, 1, 3)],
        [datetime(2000, 1, 1), datetime(1999, 12, 31)],
    )
    yield Case(
        Annotated[datetime, at.Gt(date(2000, 1, 1))],
        [date(2000, 1, 2), date(2000, 1, 3)],
        [date(2000, 1, 1), date(1999, 12, 31)],
    )
    yield Case(
        Annotated[datetime, at.Gt(Decimal('1.123'))],
        [Decimal('1.1231'), Decimal('123')],
        [Decimal('1.123'), Decimal('0')],
    )

    yield Case(Annotated[int, at.Ge(4)], (4, 5, 6, 1000, 4), (0, -1))
    yield Case(Annotated[float, at.Ge(0.5)], (0.5, 0.6, 0.7, 0.8, 0.9), (0.4, 0.0, -0.1))
    yield Case(
        Annotated[datetime, at.Ge(datetime(2000, 1, 1))],
        [datetime(2000, 1, 2), datetime(2000, 1, 3)],
        [datetime(1998, 1, 1), datetime(1999, 12, 31)],
    )

    yield Case(Annotated[int, at.Lt(4)], (0, -1), (4, 5, 6, 1000, 4))
    yield Case(Annotated[float, at.Lt(0.5)], (0.4, 0.0, -0.1), (0.5, 0.6, 0.7, 0.8, 0.9))
    yield Case(
        Annotated[datetime, at.Lt(datetime(2000, 1, 1))],
        [datetime(1999, 12, 31), datetime(1999, 12, 31)],
        [datetime(2000, 1, 2), datetime(2000, 1, 3)],
    )

    yield Case(Annotated[int, at.Le(4)], (4, 0, -1), (5, 6, 1000))
    yield Case(Annotated[float, at.Le(0.5)], (0.5, 0.0, -0.1), (0.6, 0.7, 0.8, 0.9))
    yield Case(
        Annotated[datetime, at.Le(datetime(2000, 1, 1))],
        [datetime(2000, 1, 1), datetime(1999, 12, 31)],
        [datetime(2000, 1, 2), datetime(2000, 1, 3)],
    )

    # Interval
    yield Case(Annotated[int, at.Interval(gt=4)], (5, 6, 1000), (4, 0, -1))
    yield Case(Annotated[int, at.Interval(gt=4, lt=10)], (5, 6), (4, 10, 1000, 0, -1))
    yield Case(Annotated[float, at.Interval(ge=0.5, le=1)], (0.5, 0.9, 1), (0.49, 1.1))
    yield Case(
        Annotated[datetime, at.Interval(gt=datetime(2000, 1, 1), le=datetime(2000, 1, 3))],
        [datetime(2000, 1, 2), datetime(2000, 1, 3)],
        [datetime(2000, 1, 1), datetime(2000, 1, 4)],
    )

    yield Case(Annotated[int, at.MultipleOf(multiple_of=3)], (0, 3, 9), (1, 2, 4))
    yield Case(Annotated[float, at.MultipleOf(multiple_of=0.5)], (0, 0.5, 1, 1.5), (0.4, 1.1))

    # lengths

    yield Case(Annotated[str, at.MinLen(3)], ('123', '1234', 'x' * 10), ('', '1', '12'))
    yield Case(Annotated[str, at.Len(3)], ('123', '1234', 'x' * 10), ('', '1', '12'))
    yield Case(Annotated[List[int], at.MinLen(3)], ([1, 2, 3], [1, 2, 3, 4], [1] * 10), ([], [1], [1, 2]))
    yield Case(Annotated[List[int], at.Len(3)], ([1, 2, 3], [1, 2, 3, 4], [1] * 10), ([], [1], [1, 2]))

    yield Case(Annotated[str, at.MaxLen(4)], ('', '1234'), ('12345', 'x' * 10))
    yield Case(Annotated[str, at.Len(0, 4)], ('', '1234'), ('12345', 'x' * 10))
    yield Case(Annotated[List[str], at.MaxLen(4)], ([], ['a', 'bcdef'], ['a', 'b', 'c']), (['a'] * 5, ['b'] * 10))
    yield Case(Annotated[List[str], at.Len(0, 4)], ([], ['a', 'bcdef'], ['a', 'b', 'c']), (['a'] * 5, ['b'] * 10))

    yield Case(Annotated[str, at.Len(3, 5)], ('123', '12345'), ('', '1', '12', '123456', 'x' * 10))
    yield Case(Annotated[str, at.Len(3, 3)], ('123',), ('12', '1234'))

    yield Case(Annotated[Dict[int, int], at.Len(2, 3)], [{1: 1, 2: 2}], [{}, {1: 1}, {1: 1, 2: 2, 3: 3, 4: 4}])
    yield Case(Annotated[Set[int], at.Len(2, 3)], ({1, 2}, {1, 2, 3}), (set(), {1}, {1, 2, 3, 4}))
    yield Case(Annotated[Tuple[int, ...], at.Len(2, 3)], ((1, 2), (1, 2, 3)), ((), (1,), (1, 2, 3, 4)))

    # Timezone

    yield Case(
        Annotated[datetime, at.Timezone(None)], [datetime(2000, 1, 1)], [datetime(2000, 1, 1, tzinfo=timezone.utc)]
    )
    yield Case(
        Annotated[datetime, at.Timezone(...)], [datetime(2000, 1, 1, tzinfo=timezone.utc)], [datetime(2000, 1, 1)]
    )
    yield Case(
        Annotated[datetime, at.Timezone(timezone.utc)],
        [datetime(2000, 1, 1, tzinfo=timezone.utc)],
        [datetime(2000, 1, 1), datetime(2000, 1, 1, tzinfo=timezone(timedelta(hours=6)))],
    )
    yield Case(
        Annotated[datetime, at.Timezone('Europe/London')],
        [datetime(2000, 1, 1, tzinfo=timezone(timedelta(0), name='Europe/London'))],
        [datetime(2000, 1, 1), datetime(2000, 1, 1, tzinfo=timezone(timedelta(hours=6)))],
    )

    # Quantity

    yield Case(Annotated[float, at.Unit(unit='m')], (5, 4.2), ('5m', '4.2m'))

    # predicate types

    yield Case(at.LowerCase[str], ['abc', 'foobar'], ['', 'A', 'Boom'])
    yield Case(at.UpperCase[str], ['ABC', 'DEFO'], ['', 'a', 'abc', 'AbC'])
    yield Case(at.IsDigit[str], ['123'], ['', 'ab', 'a1b2'])
    yield Case(at.IsAscii[str], ['123', 'foo bar'], ['£100', '😊', 'whatever 👀'])

    yield Case(Annotated[int, at.Predicate(lambda x: x % 2 == 0)], [0, 2, 4], [1, 3, 5])

    yield Case(at.IsFinite[float], [1.23], [math.nan, math.inf, -math.inf])
    yield Case(at.IsNotFinite[float], [math.nan, math.inf], [1.23])
    yield Case(at.IsNan[float], [math.nan], [1.23, math.inf])
    yield Case(at.IsNotNan[float], [1.23, math.inf], [math.nan])
    yield Case(at.IsInfinite[float], [math.inf], [math.nan, 1.23])
    yield Case(at.IsNotInfinite[float], [math.nan, 1.23], [math.inf])

    # check stacked predicates
    yield Case(at.IsInfinite[Annotated[float, at.Predicate(lambda x: x > 0)]], [math.inf], [-math.inf, 1.23, math.nan])

    # doc
    yield Case(Annotated[int, at.doc("A number")], [1, 2], [])

    # custom GroupedMetadata
    class MyCustomGroupedMetadata(at.GroupedMetadata):
        def __iter__(self) -> Iterator[at.Predicate]:
            yield at.Predicate(lambda x: float(x).is_integer())

    yield Case(Annotated[float, MyCustomGroupedMetadata()], [0, 2.0], [0.01, 1.5])
