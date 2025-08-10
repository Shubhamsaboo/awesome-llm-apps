from __future__ import annotations

import math
from threading import Lock
from typing import List
import numpy as np

from .func_ruin import LHNSFunction, LHNSProgram


class EliteSet:
    def __init__(self, elite_set_size, elite_set: List[LHNSProgram] | EliteSet | None = None):
        if elite_set is None:
            self._elite_set = []
        elif isinstance(elite_set, list):
            self._elite_set = elite_set
        else:
            self._elite_set = elite_set._elite_set

        self._elite_set_size = elite_set_size
        self._lock = Lock()

    def __len__(self):
        return len(self._elite_set)

    def __getitem__(self, item) -> LHNSFunction:
        return self._elite_set[item]

    def __setitem__(self, key, value):
        self._elite_set[key] = value

    @property
    def elite_set(self):
        return self._elite_set

    def update(self, function: LHNSFunction):
        elite_set = self._elite_set
        elite_set.append(function)
        elite_set = sorted(elite_set, key=lambda f: f.score, reverse=True)
        self._elite_set = elite_set[:self._elite_set_size]

    def register_function(self, func: LHNSFunction):
        # if the score is None, we still put it into the population,
        # we set the score to '-inf'
        if func.score is None:
            func.score = float('-inf')
        try:
            self._lock.acquire()
            if self.has_duplicate_function(func):
                func.score = float('-inf')
            # update: perform survival if reach the pop size
            self.update(func)
        except Exception as e:
            return
        finally:
            self._lock.release()

    def has_duplicate_function(self, func: str | LHNSFunction) -> bool:
        for f in self._elite_set:
            if str(f) == str(func) or func.score == f.score:
                return True
        return False

    def selection(self) -> LHNSFunction:
        funcs = [f for f in self._elite_set if not math.isinf(f.score)]
        return np.random.choice(funcs)
