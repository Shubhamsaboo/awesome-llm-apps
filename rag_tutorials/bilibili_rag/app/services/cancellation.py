"""长耗时操作取消支持。"""
from typing import Callable, Optional


CancelCheck = Optional[Callable[[], bool]]


class OperationCancelled(BaseException):
    """操作已被用户取消。"""


def ensure_not_cancelled(cancel_check: CancelCheck) -> None:
    if cancel_check and cancel_check():
        raise OperationCancelled()
