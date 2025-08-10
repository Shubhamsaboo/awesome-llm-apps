from __future__ import annotations

import json
import os
from threading import Lock
from typing import Optional

from .programs_database import ProgramsDatabase
from ...tools.profiler import ProfilerBase
from ...tools.profiler import TensorboardProfiler
from ...tools.profiler import WandBProfiler


class FunSearchProfiler(ProfilerBase):

    def __init__(self,
                 log_dir: Optional[str] = None,
                 *,
                 initial_num_samples=0,
                 program_db_register_interval: int = 100,
                 log_style='complex',
                 create_random_path=True,
                 **kwargs):
        """FunSearch Profiler.
        Args:
            log_dir            : the directory of current run
            initial_num_samples: the sample order start with `initial_num_samples`.
            create_random_path : create a random log_path according to evaluation_name, method_name, time, ...
        """
        super().__init__(log_dir=log_dir,
                         initial_num_samples=initial_num_samples,
                         log_style=log_style,
                         create_random_path=create_random_path,
                         **kwargs)
        self._prog_db_order = 0
        if log_dir:
            self._prog_db_path = os.path.join(self._log_dir, 'prog_db')
            os.makedirs(self._prog_db_path, exist_ok=True)
        self._intv = program_db_register_interval
        self._db_lock = Lock()

    def register_program_db(self, program_db: ProgramsDatabase):
        """Save ProgramDB to a file.
        [
            [{'score': -300, 'functions': [xxx, xxx, xxx, ...]}, {'score': -200, 'functions': [xxx, xxx, xxx, ...]}, {...}],
            [{...}, {...}],
        ]
        """
        try:
            if (self._num_samples == 0 or
                    self._num_samples % self._intv != 0):
                return
            self._db_lock.acquire()
            self._prog_db_order += 1
            isld_list = []
            for island in program_db.islands:
                clus_list = []
                for k, v in island.clusters.items():
                    funcs = [str(f) for f in v.programs]
                    func_dic = {'score': k, 'functions': funcs}
                    clus_list.append(func_dic)
                isld_list.append(clus_list)

            path = os.path.join(self._prog_db_path, f'db_{self._prog_db_order}.json')
            with open(path, 'w') as f:
                json.dump(isld_list, f)
        finally:
            if self._db_lock.locked():
                self._db_lock.release()


class FunSearchTensorboardProfiler(TensorboardProfiler, FunSearchProfiler):

    def __init__(
            self,
            *,
            log_dir: str | None = None,
            initial_num_samples=0,
            program_db_register_interval: int = 100,
            log_style='complex',
            create_random_path=True,
            **kwargs):
        """FunSearch Profiler for Tensorboard.
        Args:
            log_dir            : the directory of current run
            initial_num_samples: the sample order start with `initial_num_samples`.
            create_random_path : create a random log_path according to evaluation_name, method_name, time, ...
        """
        FunSearchProfiler.__init__(
            self, log_dir=log_dir,
            program_db_register_interval=program_db_register_interval,
            log_style=log_style,
            create_random_path=create_random_path,
            **kwargs
        )
        TensorboardProfiler.__init__(
            self, log_dir=log_dir,
            initial_num_samples=initial_num_samples,
            log_style=log_style,
            create_random_path=create_random_path,
            **kwargs
        )


class FunSearchWandbProfiler(WandBProfiler, FunSearchProfiler):
    def __init__(
            self,
            wandb_project_name: str,
            log_dir: str | None = None,
            *,
            initial_num_samples=0,
            program_db_register_interval: int = 100,
            log_style='complex',
            create_random_path=True,
            **kwargs):
        """FunSearch Profiler for Wandb.
        Args:
            wandb_project_name : the name of the wandb project
            log_dir            : the directory of current run
            initial_num_samples: the sample order start with `initial_num_samples`.
            create_random_path : create a random log_path according to evaluation_name, method_name, time, ...
            **kwargs           : kwargs for wandb
        """
        FunSearchProfiler.__init__(
            self,
            log_dir=log_dir,
            program_db_register_interval=program_db_register_interval,
            initial_num_samples=initial_num_samples,
            log_style=log_style,
            create_random_path=create_random_path,
            **kwargs
        )
        WandBProfiler.__init__(
            self,
            wandb_project_name=wandb_project_name,
            log_dir=log_dir,
            initial_num_samples=initial_num_samples,
            log_style=log_style,
            create_random_path=create_random_path,
            **kwargs
        )
