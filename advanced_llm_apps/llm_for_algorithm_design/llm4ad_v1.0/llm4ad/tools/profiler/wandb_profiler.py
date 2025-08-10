# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
# Last Revision: 2025/2/16
#
# ------------------------------- Copyright --------------------------------
# Copyright (c) 2025 Optima Group.
# 
# Permission is granted to use the LLM4AD platform for research purposes. 
# All publications, software, or other works that utilize this platform 
# or any part of its codebase must acknowledge the use of "LLM4AD" and 
# cite the following reference:
# 
# Fei Liu, Rui Zhang, Zhuoliang Xie, Rui Sun, Kai Li, Xi Lin, Zhenkun Wang, 
# Zhichao Lu, and Qingfu Zhang, "LLM4AD: A Platform for Algorithm Design 
# with Large Language Model," arXiv preprint arXiv:2412.17287 (2024).
# 
# For inquiries regarding commercial use or licensing, please contact 
# http://www.llm4ad.com/contact.html
# --------------------------------------------------------------------------

from __future__ import annotations

import sys
from typing import Optional, Literal

from ...base import Function
from .profile import ProfilerBase

try:
    import wandb
except:
    pass


class WandBProfiler(ProfilerBase):

    def __init__(self,
                 wandb_project_name: str,
                 log_dir: Optional[str] = None,
                 *,
                 initial_num_samples=0,
                 log_style='complex',
                 create_random_path=True,
                 fork_proc: Literal['auto'] | bool = 'auto',
                 **wandb_init_kwargs):
        """Weights and Biases profiler.
        Args:
            wandb_project_name : the project name in which you sync your results.
            log_dir            : the directory of current run
            initial_num_samples: the sample order start with `initial_num_samples`.
            create_random_path : create a random log_path according to evaluation_name, method_name, time, ...
            fork_proc          : whether to fork the wandb process.
        """
        super().__init__(log_dir=log_dir,
                         initial_num_samples=initial_num_samples,
                         log_style=log_style,
                         create_random_path=create_random_path,
                         **wandb_init_kwargs)

        self._wandb_project_name = wandb_project_name

        if fork_proc == 'auto':
            # for MacOS and Linux
            if sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
                setting = wandb.Settings(start_method='fork')
                self._logger_wandb = wandb.init(
                    project=self._wandb_project_name,
                    dir=self._log_dir,
                    settings=setting,
                    **wandb_init_kwargs
                )
            else:  # for Windows
                wandb.setup()
                self._logger_wandb = wandb.init(
                    project=self._wandb_project_name,
                    dir=self._log_dir,
                    **wandb_init_kwargs
                )
        elif fork_proc is True:
            setting = wandb.Settings(start_method='fork')
            self._logger_wandb = wandb.init(
                project=self._wandb_project_name,
                dir=self._log_dir,
                settings=setting,
                **wandb_init_kwargs
            )
        else:
            wandb.setup()
            self._logger_wandb = wandb.init(
                project=self._wandb_project_name,
                dir=self._log_dir,
                **wandb_init_kwargs
            )

    def get_logger(self):
        return self._logger_wandb

    def register_function(self, function: Function, program='', *, resume_mode=False):
        """Record an obtained function. This is a synchronized function.
        """
        try:
            self._register_function_lock.acquire()
            self._num_samples += 1
            self._record_and_print_verbose(function, resume_mode=resume_mode)
            self._write_wandb()
            self._write_json(function, program=program)
        finally:
            self._register_function_lock.release()

    def _write_wandb(self, *args, **kwargs):
        self._logger_wandb.log(
            {
                'Best Score of Function': self._cur_best_program_score
            },
            step=self._num_samples
        )
        self._logger_wandb.log(
            {
                'Valid Function Num': self._evaluate_success_program_num,
                'Invalid Function Num': self._evaluate_failed_program_num
            },
            step=self._num_samples
        )
        self._logger_wandb.log(
            {
                'Total Sample Time': self._tot_sample_time,
                'Total Evaluate Time': self._tot_evaluate_time
            },
            step=self._num_samples
        )

    def finish(self):
        wandb.finish()
