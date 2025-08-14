from __future__ import annotations

import math
import random
from threading import Lock
from typing import List
import numpy as np

from ...base import *


class Population:
    def __init__(self, init_pop_size, pop_size, generation=0, pop: List[Function] | Population | None = None):
        if pop is None:
            self._population = []
        elif isinstance(pop, list):
            self._population = pop
        else:
            self._population = pop._population

        self._pop_size = pop_size
        self._init_pop_size = init_pop_size
        self._lock = Lock()
        self._next_gen_pop = []
        self._generation = generation

    def __len__(self):
        return len(self._population)

    def __getitem__(self, item) -> Function:
        return self._population[item]

    def __setitem__(self, key, value):
        self._population[key] = value

    @property
    def population(self):
        return self._population

    @property
    def next_gen_pop(self):
        return self._next_gen_pop

    @property
    def generation(self):
        return self._generation

    def survival(self, pop_size: int=None):
        if pop_size is None:
            pop_size = self._pop_size

        pop = self._population + self._next_gen_pop

        # keep unique algorithms
        unique_pop = []
        unique_objectives = []
        for individual in pop:
            if individual.score not in unique_objectives:
                unique_pop.append(individual)
                unique_objectives.append(individual.score)

        pop = sorted(unique_pop, key=lambda f: f.score, reverse=True)  # better sort
        self._population = pop[:pop_size]
        self._next_gen_pop = []
        self._generation += 1

    def survival_s1(self, pop_size: int=None):
        if pop_size is None:
            pop_size = self._pop_size

        pop = self._population + self._next_gen_pop

        # keep unique algorithms
        unique_pop = []
        unique_objectives = []
        for individual in pop:
            if individual.score not in unique_objectives:
                unique_pop.append(individual)
                unique_objectives.append(individual.score)

        pop = sorted(unique_pop, key=lambda f: f.score, reverse=False)  # worst sort
        self._population = pop[:pop_size]
        self._next_gen_pop = []
        self._generation += 1

    def register_function(self, func: Function):
        # in population initialization, we only accept valid functions
        if self._generation == 0 and func.score is None:
            return
        # if the score is None, we still put it into the population,
        # we set the score to '-inf'
        if func.score is None:
            func.score = float('-inf')
        try:
            self._lock.acquire()
            # if self.has_duplicate_function(func):
            #     func.score = float('-inf')
            # register to next_gen
            self._next_gen_pop.append(func)
            # update: perform survival if reach the pop size
            if len(self._next_gen_pop) >= self._pop_size:
                self.survival()
        except Exception as e:
            return
        finally:
            self._lock.release()

    def has_duplicate_function(self, func: str | Function, pop:List[Function]=None) -> bool:
        if pop is None:
            pop = self._population
        for f in pop:
            if str(f) == str(func) or func.score == f.score:
                return True
        for f in self._next_gen_pop:
            if str(f) == str(func) or func.score == f.score:
                return True
        return False

    def selection(self, pop:List[Function]=None) -> Function:
        if pop is None:
            pop = self._population
        funcs = [f for f in pop if not math.isinf(f.score)]
        func = sorted(funcs, key=lambda f: f.score, reverse=True)
        p = [1 / (r + 1 + len(func)) for r in range(len(func))]
        p = np.array(p)
        p = p / np.sum(p)
        return np.random.choice(func, p=p)

    def selection_e1(self, pop:List[Function]=None) -> Function:
        if pop is None:
            pop = self._population
        funcs = [f for f in pop if not math.isinf(f.score)]
        func = sorted(funcs, key=lambda f: f.score, reverse=True)
        probs = [1 for _ in range(len(pop))]
        return np.random.choice(func, p=probs)
