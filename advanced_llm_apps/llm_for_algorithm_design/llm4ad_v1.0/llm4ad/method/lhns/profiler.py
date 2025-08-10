from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from threading import Lock
from typing import List, Dict, Optional

try:
    import wandb
except:
    pass

from .elite_set import EliteSet
from .func_ruin import LHNSFunction
from ...tools.profiler import TensorboardProfiler, ProfilerBase, WandBProfiler


class LHNSProfiler(ProfilerBase):
    _cur_gen = 0

    def __init__(self,
                 log_dir: Optional[str] = None,
                 *,
                 evaluation_name='Problem',
                 method_name='LHNS',
                 initial_num_samples=0,
                 log_style='complex',
                 create_random_path=True,
                 **kwargs):
        """LHNS Profiler
        Args:
            log_dir            : the directory of current run
            evaluation_name    : the name of the evaluation instance (the name of the problem to be solved).
            method_name        : the name of the search method.
            initial_num_samples: the sample order start with `initial_num_samples`.
            create_random_path : create a random log_path according to evaluation_name, method_name, time, ...
        """
        super().__init__(evaluation_name=evaluation_name,
                         method_name=method_name,
                         log_dir=log_dir,
                         initial_num_samples=initial_num_samples,
                         log_style=log_style,
                         create_random_path=create_random_path,
                         **kwargs)
        self._pop_lock = Lock()
        if self._log_dir:
            self._ckpt_dir = os.path.join(self._log_dir, 'population')
            os.makedirs(self._ckpt_dir, exist_ok=True)

    def _write_json(self, function: LHNSFunction, *, record_type='history', record_sep=200):
        """Write function data to a JSON file.
        Args:
            function   : The function object containing score and string representation.
            record_type: Type of record, 'history' or 'best'. Defaults to 'history'.
            record_sep : Separator for history records. Defaults to 200.
        """
        assert record_type in ['history', 'best']

        if not self._log_dir:
            return

        sample_order = getattr(self.__class__, '_num_samples', 0)
        content = {
            'sample_order': sample_order,
            'algorithm': function.algorithm,  # Added when recording
            'function': str(function),
            'features': function.features,
            'score': function.score
        }

        if record_type == 'history':
            lower_bound = ((sample_order - 1) // record_sep) * record_sep
            upper_bound = lower_bound + record_sep
            filename = f'samples_{lower_bound + 1}~{upper_bound}.json'
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


class LHNSTensorboardProfiler(TensorboardProfiler, LHNSProfiler):

    def __init__(self,
                 log_dir: str | None = None,
                 *,
                 evaluation_name='Problem',
                 method_name='LHNS',
                 initial_num_samples=0,
                 log_style='complex',
                 create_random_path=True,
                 **kwargs):
        """LHNS Profiler for Tensorboard.
        Args:
            log_dir            : the directory of current run
            evaluation_name    : the name of the evaluation instance (the name of the problem to be solved).
            method_name        : the name of the search method.
            initial_num_samples: the sample order start with `initial_num_samples`.
            create_random_path : create a random log_path according to evaluation_name, method_name, time, ...
            **kwargs           : kwargs for wandb
        """
        LHNSProfiler.__init__(
            self, log_dir=log_dir,
            evaluation_name=evaluation_name,
            create_random_path=create_random_path,
            method_name=method_name,
            **kwargs
        )
        TensorboardProfiler.__init__(
            self,
            log_dir=log_dir,
            evaluation_name=evaluation_name,
            method_name=method_name,
            initial_num_samples=initial_num_samples,
            log_style=log_style,
            create_random_path=create_random_path,
            **kwargs
        )

    def finish(self):
        if self._log_dir:
            self._writer.close()

        filename = 'end.json'
        path = os.path.join(os.path.join(self._log_dir, 'population'), filename)

        with open(path, 'w') as json_file:
            json.dump([], json_file, indent=4)


class LHNSWandbProfiler(WandBProfiler, LHNSProfiler):
    _cur_gen = 0

    def __init__(self,
                 wandb_project_name: str,
                 log_dir: str | None = None,
                 *,
                 evaluation_name='Problem',
                 method_name='LHNS',
                 initial_num_samples=0,
                 log_style='complex',
                 create_random_path=True,
                 **kwargs):
        """LHNS Profiler for Wandb.
        Args:
            wandb_project_name : the name of the wandb project
            log_dir            : the directory of current run
            evaluation_name    : the name of the evaluation instance (the name of the problem to be solved).
            method_name        : the name of the search method.
            initial_num_samples: the sample order start with `initial_num_samples`.
            create_random_path : create a random log_path according to evaluation_name, method_name, time, ...
            **kwargs           : kwargs for wandb
        """
        LHNSProfiler.__init__(
            self,
            log_dir=log_dir,
            evaluation_name=evaluation_name,
            create_random_path=create_random_path,
            method_name=method_name,
            **kwargs
        )
        WandBProfiler.__init__(
            self,
            wandb_project_name=wandb_project_name,
            log_dir=log_dir,
            evaluation_name=evaluation_name,
            method_name=method_name,
            initial_num_samples=initial_num_samples,
            log_style=log_style,
            create_random_path=create_random_path,
            **kwargs
        )
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
