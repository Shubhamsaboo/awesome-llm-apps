# Module Name: LHNS
# Last Revision: 2025/2/16
# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Reference:
#   - Fei Liu, Tong Xialiang, Mingxuan Yuan, Xi Lin, Fu Luo, Zhenkun Wang, Zhichao Lu, and Qingfu Zhang.
#       "Evolution of Heuristics: Towards Efficient Automatic Algorithm Design Using Large Language Model."
#       In Forty-first International Conference on Machine Learning (ICML). 2024.
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

import concurrent.futures
import copy
import random
import time
import traceback
from threading import Thread
from typing import Optional, Literal

import numpy as np

from .elite_set import EliteSet
from .func_ruin import LHNSFunctionRuin, LHNSFunction, LHNSProgram, LHNSTextFunctionProgramConverter
from .profiler import LHNSProfiler
from .prompt import LHNSPrompt
from .sampler import LHNSSampler
from ...base import (
    Evaluation, LLM, SecureEvaluator
)
from ...tools.profiler import ProfilerBase


class LHNS:
    def __init__(self,
                 llm: LLM,
                 evaluation: Evaluation,
                 profiler: ProfilerBase = None,
                 max_sample_nums: Optional[int] = 100,
                 cooling_rate: float = 0.1,
                 elite_set_size: int = 5,
                 method: str = 'vns',  # vns, ils, ts
                 num_samplers: int = 1,
                 num_evaluators: int = 1,
                 *,
                 resume_mode: bool = False,
                 debug_mode: bool = False,
                 multi_thread_or_process_eval: Literal['thread', 'process'] = 'thread',
                 **kwargs):
        """Evolutionary of Heuristics.
        Args:
            llm             : an instance of 'llm4ad.base.LLM', which provides the way to query LLM.
            evaluation      : an instance of 'llm4ad.base.Evaluator', which defines the way to calculate the score of a generated function.
            profiler        : an instance of 'llm4ad.method.eoh.LHNSProfiler'. If you do not want to use it, you can pass a 'None'.
            max_generations : terminate after evolving 'max_generations' generations or reach 'max_sample_nums',
                              pass 'None' to disable this termination condition.
            max_sample_nums : terminate after evaluating max_sample_nums functions (no matter the function is valid or not) or reach 'max_generations',
                              pass 'None' to disable this termination condition.
            pop_size        : population size, if set to 'None', LHNS will automatically adjust this parameter.
            selection_num   : number of selected individuals while crossover.
            use_e2_operator : if use e2 operator.
            use_m1_operator : if use m1 operator.
            use_m2_operator : if use m2 operator.
            resume_mode     : in resume_mode, randsample will not evaluate the template_program, and will skip the init process. TODO: More detailed usage.
            debug_mode      : if set to True, we will print detailed information.
            multi_thread_or_process_eval: use 'concurrent.futures.ThreadPoolExecutor' or 'concurrent.futures.ProcessPoolExecutor' for the usage of
                multi-core CPU while evaluation. Please note that both settings can leverage multi-core CPU. As a result on my personal computer (Mac OS, Intel chip),
                setting this parameter to 'process' will faster than 'thread'. However, I do not sure if this happens on all platform so I set the default to 'thread'.
                Please note that there is one case that cannot utilize multi-core CPU: if you set 'safe_evaluate' argument in 'evaluator' to 'False',
                and you set this argument to 'thread'.
            **kwargs                    : some args pass to 'llm4ad.base.SecureEvaluator'. Such as 'fork_proc'.
        """
        self._template_program_str = evaluation.template_program
        self._task_description_str = evaluation.task_description
        self._cooling_rate = float(cooling_rate)
        self._max_sample_nums = max_sample_nums

        # samplers and evaluators
        self._num_samplers = num_samplers
        self._num_evaluators = num_evaluators
        self._resume_mode = resume_mode
        self._debug_mode = debug_mode
        llm.debug_mode = debug_mode
        self._multi_thread_or_process_eval = multi_thread_or_process_eval

        # function to be evolved
        self._current_function: LHNSFunction = LHNSTextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._best_function: LHNSFunction = LHNSTextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._function_to_evolve: LHNSFunction = LHNSTextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._function_to_evolve_name: str = self._function_to_evolve.name
        self._template_program: LHNSProgram = LHNSTextFunctionProgramConverter.text_to_program(self._template_program_str)

        # elite set, sampler, and evaluator
        self._method = method
        self._elite_set = EliteSet(elite_set_size=elite_set_size)
        self._sampler = LHNSSampler(llm, self._template_program_str)
        self._evaluator = SecureEvaluator(evaluation, debug_mode=debug_mode, **kwargs)
        self._profiler = profiler

        # statistics
        self._tot_sample_nums = 0

        # reset _initial_sample_nums_max
        self._initial_sample_nums_max = 20

        # multi-thread executor for evaluation
        assert multi_thread_or_process_eval in ['thread', 'process']
        if multi_thread_or_process_eval == 'thread':
            self._evaluation_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=num_evaluators
            )
        else:
            self._evaluation_executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=num_evaluators
            )

        # pass parameters to profiler
        if profiler is not None:
            self._profiler.record_parameters(llm, evaluation, self)

    def _sample_evaluate_register(self, prompt) -> LHNSFunction:
        """Perform following steps:
        1. Sample an algorithm using the given prompt.
        2. Evaluate it by submitting to the process/thread pool, and get the results.
        3. Add the function to the population and register it to the profiler.
        """
        sample_start = time.time()
        thought, func = self._sampler.get_thought_and_function(prompt)
        sample_time = time.time() - sample_start
        if thought is None or func is None:
            return
        # convert to Program instance
        program = LHNSTextFunctionProgramConverter.function_to_program(func, self._template_program)
        if program is None:
            return
        # evaluate
        score, eval_time = self._evaluation_executor.submit(
            self._evaluator.evaluate_program_record_time,
            program
        ).result()
        # register to profiler
        func.score = score
        func.evaluate_time = eval_time
        func.algorithm = thought
        func.sample_time = sample_time
        if self._profiler is not None:
            self._profiler.register_function(func)
            self._tot_sample_nums += 1

        return func


    def _continue_loop(self) -> bool:
        if self._max_sample_nums is None:
            return True
        else:
            return self._tot_sample_nums < self._max_sample_nums

    def simulated_annealing(self, next_func: LHNSFunction, cooling_rate: float, trans_count: int) -> (bool, int):
        temperature = cooling_rate * (1 - (self._tot_sample_nums - 1) / self._max_sample_nums)

        if next_func.score is None or next_func.score == float("-inf"):
            trans_count += 1
            return False, trans_count

        if next_func.score < self._current_function.score:
            temp_value = (-abs(self._current_function.score - next_func.score) / (self._current_function.score + 1E-10)) / temperature
            if np.random.rand() < np.exp(temp_value):
                accept = True
            else:
                accept = False
            trans_count += 1
        else:
            accept = True
            trans_count = 0

        return accept, trans_count

    def method_vns(self):

        initial_rate = self._cooling_rate
        cooling_rate = initial_rate
        trans_count = 0

        while self._continue_loop():
            try:
                prompt = LHNSPrompt.get_prompt_rr(self._task_description_str, self._current_function, cooling_rate, self._function_to_evolve)
                if self._debug_mode:
                    print(f'VNS RR Prompt: {prompt}')
                new_func = self._sample_evaluate_register(prompt)
                accept, trans_count = self.simulated_annealing(new_func, cooling_rate, trans_count)

                if accept:
                    self._current_function = new_func
                    cooling_rate = self._cooling_rate
                    if self._current_function.score > self._best_function.score:
                        self._best_function = self._current_function
                else:
                    if cooling_rate < 1.0:
                        cooling_rate += 0.1
                    else:
                        cooling_rate = self._cooling_rate

                if not self._continue_loop():
                    break


            except KeyboardInterrupt:
                break
            except Exception as e:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

        # shutdown evaluation_executor
        try:
            self._evaluation_executor.shutdown(cancel_futures=True)
        except:
            pass

    def method_ils(self):

        cooling_rate = self._cooling_rate
        trans_count = 0

        while self._continue_loop():
            try:
                if trans_count >= 10:
                    prompt = LHNSPrompt.get_prompt_m(self._task_description_str, self._best_function,
                                                     self._function_to_evolve)
                    if self._debug_mode:
                        print(f'ILS M Prompt: {prompt}')
                else:
                    prompt = LHNSPrompt.get_prompt_rr(self._task_description_str, self._current_function, cooling_rate,
                                                      self._function_to_evolve)
                    if self._debug_mode:
                        print(f'ILS RR Prompt: {prompt}')

                new_func = self._sample_evaluate_register(prompt)
                accept, trans_count = self.simulated_annealing(new_func, cooling_rate, trans_count)

                if accept:
                    self._current_function = new_func
                    if self._current_function.score > self._best_function.score:
                        self._best_function = self._current_function

                if not self._continue_loop():
                    break


            except KeyboardInterrupt:
                break
            except Exception as e:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

        # shutdown evaluation_executor
        try:
            self._evaluation_executor.shutdown(cancel_futures=True)
        except:
            pass

    def method_ts(self):

        cooling_rate = self._cooling_rate
        trans_count = 0

        while self._continue_loop():
            try:
                if trans_count >= 10:
                    prev_func = self._elite_set.selection()
                    prompt = LHNSPrompt.get_prompt_merge(self._task_description_str, self._current_function, prev_func,
                                                     self._function_to_evolve)
                    if self._debug_mode:
                        print(f'TS M Prompt: {prompt}')
                else:
                    prompt = LHNSPrompt.get_prompt_rr(self._task_description_str, self._current_function, cooling_rate,
                                                      self._function_to_evolve)
                    if self._debug_mode:
                        print(f'TS RR Prompt: {prompt}')

                new_func = self._sample_evaluate_register(prompt)
                self._current_function.features = LHNSFunctionRuin.find_code_features(self._current_function, new_func)
                self._elite_set.update(new_func)
                accept, trans_count = self.simulated_annealing(new_func, cooling_rate, trans_count)

                if accept:
                    self._current_function = new_func
                    if self._current_function.score > self._best_function.score:
                        self._best_function = self._current_function

                if not self._continue_loop():
                    break


            except KeyboardInterrupt:
                break
            except Exception as e:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

        # shutdown evaluation_executor
        try:
            self._evaluation_executor.shutdown(cancel_futures=True)
        except:
            pass

    def _iteratively_use_lhns_operator(self):

        assert self._method in ['vns', 'ils', 'ts'], f'None defined method: {self._method}'

        if self._method == 'vns':
            self.method_vns()
        elif self._method == 'ils':
            self.method_ils()
        elif self._method == 'ts':
            self.method_ts()

    def _iteratively_init(self):

        trials = 1
        while True:
            try:
                # get a new func using i1
                prompt = LHNSPrompt.get_prompt_i1(self._task_description_str, self._function_to_evolve)
                self._current_function = self._sample_evaluate_register(prompt)
                if self._current_function.score != float('-inf') or self._current_function.score is not None:
                    self._best_function = copy.deepcopy(self._current_function)
                    self._elite_set.update(self._current_function)
                    print(f'Note: During initialization, LHNS gets initial valid algorithm '
                          f'after {trials} trails.')
                    break
                trials += 1
                assert trials < self._initial_sample_nums_max
            except Exception:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

    def _multi_threaded_sampling(self, fn: callable, *args, **kwargs):
        """Execute `fn` using multithreading.
        In LHNS, `fn` can be `self._iteratively_init_population` or `self._iteratively_use_eoh_operator`.
        """
        # threads for sampling
        sampler_threads = [
            Thread(target=fn, args=args, kwargs=kwargs)
            for _ in range(self._num_samplers)
        ]
        for t in sampler_threads:
            t.start()
        for t in sampler_threads:
            t.join()

    def run(self):
        if not self._resume_mode:
            # do initialization
            self._multi_threaded_sampling(self._iteratively_init)
        # evolutionary search
        self._multi_threaded_sampling(self._iteratively_use_lhns_operator)
        # finish
        if self._profiler is not None:
            self._profiler.finish()
