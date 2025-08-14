from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from threading import Lock
from typing import List, Dict

import numpy as np

try:
    import wandb
except:
    pass

from .population import Population
from ...base import Function
from ...tools.profiler import TensorboardProfiler, ProfilerBase, WandBProfiler


class MOEADProfiler(ProfilerBase):

    def __init__(self,
                 log_dir: str | None = None,
                 num_objs=2,
                 *,
                 initial_num_samples=0,
                 log_style='complex',
                 **kwargs):
        super().__init__(log_dir=log_dir,
                         initial_num_samples=initial_num_samples,
                         log_style=log_style,
                         num_objs=num_objs,
                         **kwargs)
        self._cur_gen = 0
        self._pop_lock = Lock()
        if self._log_dir:
            self._ckpt_dir = os.path.join(self._log_dir, 'population')
            self._elitist_dir = os.path.join(self._log_dir, 'elitist')
            os.makedirs(self._ckpt_dir, exist_ok=True)
            os.makedirs(self._elitist_dir, exist_ok=True)

    def register_population(self, pop: Population):
        try:
            self._pop_lock.acquire()
            if (self._num_samples == 0 or
                    pop.generation == self._cur_gen):
                return
            funcs = pop.population  # type: List[Function]
            funcs_json = []  # type: List[Dict]
            for f in funcs:
                f_score = f.score
                if f.score is not None:
                    if np.isinf(np.array(f.score)).any():
                        f_score = None
                    else:
                        f_score = f_score.tolist()
                f_json = {
                    'algorithm': f.algorithm,
                    'function': str(f),
                    'score': f_score
                }
                funcs_json.append(f_json)
            path = os.path.join(self._ckpt_dir, f'pop_{pop.generation}.json')
            with open(path, 'w') as json_file:
                json.dump(funcs_json, json_file, indent=4)

            # Saving the elitist
            funcs = pop.elitist
            for f in funcs:
                f_score = f.score
                if f.score is not None:
                    if np.isinf(np.array(f.score)).any():
                        f_score = None
                    else:
                        f_score = f_score.tolist()
                f_json = {
                    'algorithm': f.algorithm,
                    'function': str(f),
                    'score': f_score
                }
                funcs_json.append(f_json)
            path = os.path.join(self._elitist_dir, f'elitist_{pop.generation}.json')
            with open(path, 'w') as json_file:
                json.dump(funcs_json, json_file, indent=4)
            self._cur_gen += 1
        finally:
            if self._pop_lock.locked():
                self._pop_lock.release()

    def _write_json(self, function: Function, program='', *, record_type='history', record_sep=200):
        """
            Write function data to a JSON file.

            Parameters:
                function (Function): The function object containing score and string representation.
                record_type (str, optional): Type of record, 'history' or 'best'. Defaults to 'history'.
                record_sep (int, optional): Separator for history records. Defaults to 200.
        """
        assert record_type in ['history', 'best']

        if not self._log_dir:
            return

        sample_order = self._num_samples
        func_score = function.score
        if function.score is not None:
            if np.isinf(np.array(function.score)).any():
                func_score = None
            else:
                func_score = func_score.tolist()
        content = {
            'sample_order': sample_order,
            'algorithm': function.algorithm,  # Added when recording
            'function': str(function),
            'score': func_score,
            'program': program,
        }

        if record_type == 'history':
            lower_bound = (sample_order // record_sep) * record_sep
            upper_bound = lower_bound + record_sep
            filename = f'samples_{lower_bound}~{upper_bound}.json'
        else:
            filename = 'samples_best.json'

        path = os.path.join(self._samples_json_dir, filename)

        try:
            with open(path, 'r') as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(content)
        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent=4)


class MOEADTensorboardProfiler(TensorboardProfiler, MOEADProfiler):

    def __init__(self,
                 log_dir: str | None = None,
                 *,
                 initial_num_samples=0,
                 log_style='complex',
                 **kwargs):
        MOEADProfiler.__init__(self,
                               log_dir=log_dir,
                               **kwargs)
        TensorboardProfiler.__init__(self, log_dir=log_dir,
                                     initial_num_samples=initial_num_samples,
                                     log_style=log_style, **kwargs)

    def finish(self):
        if self._log_dir:
            self._writer.close()

        filename = 'end.json'
        path = os.path.join(os.path.join(self._log_dir, 'population'), filename)

        with open(path, 'w') as json_file:
            json.dump([], json_file, indent=4)


class MOEADWandbProfiler(WandBProfiler, MOEADProfiler):

    def __init__(self,
                 wandb_project_name: str,
                 log_dir: str | None = None,
                 *,
                 initial_num_samples=0,
                 log_style='complex',
                 **kwargs):
        MOEADProfiler.__init__(self, log_dir=log_dir,
                               **kwargs)
        WandBProfiler.__init__(self,
                               wandb_project_name=wandb_project_name,
                               log_dir=log_dir,
                               initial_num_samples=initial_num_samples,
                               log_style=log_style, **kwargs)
        self._pop_lock = Lock()
        if self._log_dir:
            self._ckpt_dir = os.path.join(self._log_dir, 'population')
            os.makedirs(self._ckpt_dir, exist_ok=True)

    def finish(self):
        wandb.finish()
        filename = 'end.json'
        path = os.path.join(os.path.join(self._log_dir, 'population'), filename)

        with open(path, 'w') as json_file:
            json.dump([], json_file, indent=4)
