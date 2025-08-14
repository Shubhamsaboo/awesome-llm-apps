from __future__ import annotations

import math
from threading import Lock
from typing import List
import numpy as np
import traceback

from ...base import *
from codebleu.syntax_match import calc_syntax_match
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting


class Population:
    def __init__(self, pop_size, generation=0, pop: List[Function] | Population | None = None):
        if pop is None:
            self._population = []
        elif isinstance(pop, list):
            self._population = pop
        else:
            self._population = pop._population

        self._pop_size = pop_size
        self._lock = Lock()
        self._next_gen_pop = []
        self._elitist = []
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
    def elitist(self):
        return self._elitist

    @property
    def generation(self):
        return self._generation

    def register_function(self, func: Function):
        # we only accept valid functions
        if func.score is None:
            return
        try:
            self._lock.acquire()
            # register to next_gen
            if not self.has_duplicate_function(func):
                self._next_gen_pop.append(func)

            # update: perform survival if reach the pop size
            if len(self._next_gen_pop) >= self._pop_size or (len(self._next_gen_pop) >= self._pop_size // 4 and self._generation == 0):
                pop = self._population + self._next_gen_pop

                pop_elitist = pop + self._elitist
                objs = [ind.score for ind in pop_elitist]
                objs_array = -np.array(objs)
                nondom_idx = NonDominatedSorting().do(objs_array, only_non_dominated_front=True)
                self._elitist = []
                for idx in nondom_idx.tolist():
                    self._elitist.append(pop_elitist[idx])

                crt_pop_size = len(pop)
                dominated_counts = np.zeros((crt_pop_size, crt_pop_size))
                for i in range(crt_pop_size):
                    for j in range(i + 1, crt_pop_size):
                        if (np.array(pop[i].score) >= np.array(pop[j].score)).all():
                            dominated_counts[i, j] = -calc_syntax_match([pop[i].entire_code], pop[j].entire_code, 'python')
                        elif (np.array(pop[j].score) >= np.array(pop[i].score)).all():
                            dominated_counts[j, i] = -calc_syntax_match([pop[j].entire_code], pop[i].entire_code, 'python')
                dominated_counts_ = dominated_counts.sum(0)
                self._population = [pop[i] for i in np.argsort(-dominated_counts_)[:self._pop_size // 5]]  # minus for descending, //5 for keep the original pop_size
                self._next_gen_pop = []
                self._generation += 1
        except Exception as e:
            traceback.print_exc()
            return
        finally:
            self._lock.release()

    def has_duplicate_function(self, func: str | Function) -> bool:
        if func.score is None:
            return True

        for i in range(len(self._population)):
            f = self._population[i]
            if str(f) == str(func):
                if func.score[0] > f.score[0]:
                    self._population[i] = func
                    return True
                if func.score[0] == f.score[0] and func.score[1] > f.score[1]:
                    self._population[i] = func
                    return True

        for i in range(len(self._next_gen_pop)):
            f = self._next_gen_pop[i]
            if str(f) == str(func):
                if func.score[0] > f.score[0]:
                    self._next_gen_pop[i] = func
                    return True
                if func.score[0] == f.score[0] and func.score[1] > f.score[1]:
                    self._next_gen_pop[i] = func
                    return True
        return False

    def selection(self) -> Function:
        # funcs = [f for f in self._population if not math.isinf(f.score)]
        funcs = [f for f in self._population if not np.isinf(np.array(f.score)).any()]

        # AST
        if len(funcs) > 0:
            crt_pop_size = len(funcs)
            dominated_counts = np.zeros((crt_pop_size, crt_pop_size))
            for i in range(crt_pop_size):
                for j in range(i + 1, crt_pop_size):
                    if (np.array(funcs[i].score) >= np.array(funcs[j].score)).all():
                        dominated_counts[i, j] = -calc_syntax_match([funcs[i].entire_code], funcs[j].entire_code, 'python')
                    elif (np.array(funcs[j].score) >= np.array(funcs[i].score)).all():
                        dominated_counts[j, i] = -calc_syntax_match([funcs[j].entire_code], funcs[i].entire_code, 'python')
            dominated_counts_ = dominated_counts.sum(0)
            p = np.exp(dominated_counts_) / np.exp(dominated_counts_).sum()

        return np.random.choice(funcs, p=p, replace=False)
