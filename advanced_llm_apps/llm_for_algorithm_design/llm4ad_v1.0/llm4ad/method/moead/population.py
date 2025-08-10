from __future__ import annotations

import math
from threading import Lock
from typing import List
import numpy as np
import traceback

from ...base import *
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
        # TODO: only to 2 objectives
        w1 = np.linspace(0, 1, self._pop_size//5)
        self._weight_vectors = np.array([w1, 1 - w1])
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
            if len(self._next_gen_pop) >= self._pop_size or (len(self._next_gen_pop) >= self._pop_size//5 and self._generation == 0):
                pop = self._population + self._next_gen_pop

                pop_elitist = pop + self._elitist
                objs = [ind.score for ind in pop_elitist]
                objs_array = -np.array(objs)
                nondom_idx = NonDominatedSorting().do(objs_array, only_non_dominated_front=True)
                self._elitist = []
                for idx in nondom_idx.tolist():
                    self._elitist.append(pop_elitist[idx])

                crt_pop_size = len(pop)
                selected_idx_list = []
                for i in range(self._pop_size//5):
                    best_sub_score = float('-inf')
                    best_sub_idx = None
                    for j in range(crt_pop_size):
                        sub_score = -np.max(-self._weight_vectors[:, i] * np.array(pop[j].score)) # TCH
                        if best_sub_score < sub_score and np.isfinite(sub_score):
                            best_sub_score = sub_score
                            best_sub_idx = j
                    selected_idx_list.append(best_sub_idx)
                self._population = [pop[i] for i in selected_idx_list]
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

    def selection(self, pref: np.array) -> Function:
        funcs = [f for f in self._population if not np.isinf(np.array(f.score)).any()]

        crt_pop_size = len(funcs)
        sub_score_list = []
        sub_idx_list = []
        for j in range(crt_pop_size):
            sub_score = -np.max(-pref * np.array(funcs[j].score)) # TCH
            if np.isfinite(sub_score):
                sub_score_list.append(sub_score)
                sub_idx_list.append(j)
        sub_score_list = np.array(sub_score_list)
        sub_idx_list = np.array(sub_idx_list)
        sorted_idx = np.argsort(-sub_score_list) # minus for descending
        sub_idx_list = sub_idx_list[sorted_idx]
        func = [funcs[i] for i in sub_idx_list]
        p = [1 / (r + len(func)) for r in range(len(func))]
        p = np.array(p)
        p = p / np.sum(p)
        return np.random.choice(func, p=p, replace=False)
