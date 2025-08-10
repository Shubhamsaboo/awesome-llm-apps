# Module Name: MOEA/D
# Last Revision: 2025/2/16
# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Reference:
#   - Shunyu Yao, Fei Liu, Xi Lin, Zhichao Lu, Zhenkun Wang, and Qingfu Zhang.
#       "Multi-objective evolution of heuristic using large language model."
#       In Proceedings of the AAAI Conference on Artificial Intelligence, 2025.
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
import sys
import time
import traceback
from threading import Thread
import numpy as np

from .population import Population
from .profiler import MOEADProfiler
from .prompt import MOEADPrompt
from .sampler import MOEADSampler
from ...base import (
    Evaluation, LLM, Function, Program, TextFunctionProgramConverter, SecureEvaluator
)
from ...tools.profiler import ProfilerBase


class MOEAD:
    def __init__(self,
                 llm: LLM,
                 evaluation: Evaluation,
                 profiler: ProfilerBase = None,
                 max_generations: int | None = 10,
                 max_sample_nums: int | None = 100,
                 pop_size: int = 20,
                 selection_num=5,
                 use_e2_operator: bool = True,
                 use_m1_operator: bool = True,
                 use_m2_operator: bool = True,
                 num_samplers: int = 1,
                 num_evaluators: int = 1,
                 num_objs: int = 2,
                 *,
                 resume_mode: bool = False,
                 initial_sample_num: int | None = None,
                 debug_mode: bool = False,
                 multi_thread_or_process_eval: str = 'thread',
                 **kwargs):
        """
        Args:
            llm             : an instance of 'llm4ad.base.LLM', which provides the way to query LLM.
            evaluation      : an instance of 'llm4ad.base.Evaluator', which defines the way to calculate the score of a generated function.
            profiler        : an instance of 'llm4ad.method.moead.MOEADProfiler'. If you do not want to use it, you can pass a 'None'.
            max_generations : terminate after evolving 'max_generations' generations or reach 'max_sample_nums'.
            max_sample_nums : terminate after evaluating max_sample_nums functions (no matter the function is valid or not) or reach 'max_generations'.
            pop_size        : population size.
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
            **kwargs        : some args pass to 'llm4ad.base.SecureEvaluator'. Such as 'fork_proc'.
        """
        self._template_program_str = evaluation.template_program
        self._task_description_str = evaluation.task_description
        self._num_objs = num_objs
        self._max_generations = max_generations
        self._max_sample_nums = max_sample_nums
        self._pop_size = pop_size
        self._selection_num = selection_num
        self._use_e2_operator = use_e2_operator
        self._use_m1_operator = use_m1_operator
        self._use_m2_operator = use_m2_operator
        self._num_samplers = num_samplers
        self._num_evaluators = num_evaluators
        self._resume_mode = resume_mode
        self._initial_sample_num = initial_sample_num
        self._debug_mode = debug_mode
        self._multi_thread_or_process_eval = multi_thread_or_process_eval

        # function to be evolved
        self._function_to_evolve: Function = TextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._function_to_evolve_name: str = self._function_to_evolve.name
        self._template_program: Program = TextFunctionProgramConverter.text_to_program(self._template_program_str)

        # population, sampler, and evaluator
        self._population = Population(pop_size=self._pop_size)
        llm.debug_mode = debug_mode
        self._sampler = MOEADSampler(llm, self._template_program_str)
        self._evaluator = SecureEvaluator(evaluation, debug_mode=debug_mode, **kwargs)
        self._profiler = profiler
        if profiler is not None:
            self._profiler.record_parameters(llm, evaluation, self)  # ZL: Necessary

        # statistics
        self._tot_sample_nums = 0 if initial_sample_num is None else initial_sample_num

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

    def _sample_evaluate_register(self, prompt):
        """Sample a function using the given prompt -> evaluate it by submitting to the process/thread pool ->
        add the function to the population and register it to the profiler.
        """
        sample_start = time.time()
        thought, func = self._sampler.get_thought_and_function(prompt)
        sample_time = time.time() - sample_start
        if thought is None or func is None:
            return

        # convert to Program instance
        program = TextFunctionProgramConverter.function_to_program(func, self._template_program)
        if program is None:
            return

        # evaluate
        score, eval_time = self._evaluation_executor.submit(
            self._evaluator.evaluate_program_record_time,
            program
        ).result()

        # score
        func.score = score
        func.evaluate_time = eval_time
        func.algorithm = thought
        func.sample_time = sample_time
        try:
            if self._profiler is not None:
                self._profiler.register_function(func, program=str(program))
                if isinstance(self._profiler, MOEADProfiler):
                    self._profiler.register_population(self._population)
                self._tot_sample_nums += 1
        except Exception as e:
            traceback.print_exc()

        # register to the population
        self._population.register_function(func)

    def _continue_sample(self):
        """Check if it meets the max_sample_nums restrictions.
        """
        if self._max_generations is None and self._max_sample_nums is None:
            return True
        if self._max_generations is None and self._max_sample_nums is not None:
            if self._tot_sample_nums < self._max_sample_nums:
                return True
            else:
                return False
        if self._max_generations is not None and self._max_sample_nums is None:
            if self._population.generation < self._max_generations:
                return True
            else:
                return False
        if self._max_generations is not None and self._max_sample_nums is not None:
            continue_until_reach_gen = False
            continue_until_reach_sample = False
            if self._population.generation < self._max_generations:
                continue_until_reach_gen = True
            if self._tot_sample_nums < self._max_sample_nums:
                continue_until_reach_sample = True
            return continue_until_reach_gen and continue_until_reach_sample

    def _thread_do_evolutionary_operator(self):
        while self._continue_sample():
            try:
                for i in range(self._pop_size):
                    crt_pref = self._population._weight_vectors[:, i]
                    # get a new func using e1
                    indivs = [self._population.selection(crt_pref) for _ in range(self._selection_num)]
                    prompt = MOEADPrompt.get_prompt_e1(self._task_description_str, indivs, self._function_to_evolve)

                    if self._debug_mode:
                        print(prompt)
                        input()

                    self._sample_evaluate_register(prompt)
                    if not self._continue_sample():
                        break

                    # get a new func using e2
                    if self._use_e2_operator:
                        indivs = [self._population.selection(crt_pref) for _ in range(self._selection_num)]
                        prompt = MOEADPrompt.get_prompt_e2(self._task_description_str, indivs, self._function_to_evolve)

                        if self._debug_mode:
                            print(prompt)
                            input()

                        self._sample_evaluate_register(prompt)
                        if not self._continue_sample():
                            break

                    # get a new func using m1
                    if self._use_m1_operator:
                        indiv = self._population.selection(crt_pref)
                        prompt = MOEADPrompt.get_prompt_m1(self._task_description_str, indiv, self._function_to_evolve)

                        if self._debug_mode:
                            print(prompt)
                            input()

                        self._sample_evaluate_register(prompt)
                        if not self._continue_sample():
                            break

                    # get a new func using m2
                    if self._use_m2_operator:
                        indiv = self._population.selection(crt_pref)
                        prompt = MOEADPrompt.get_prompt_m2(self._task_description_str, indiv, self._function_to_evolve)

                        if self._debug_mode:
                            print(prompt)
                            input()

                        self._sample_evaluate_register(prompt)
                        if not self._continue_sample():
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

    def _thread_init_population(self):
        """Let a thread repeat {sample -> evaluate -> register to population}
        to initialize a population.
        """
        while self._population.generation == 0:
            if not self._continue_sample():
                break
            try:
                # get a new func using i1
                prompt = MOEADPrompt.get_prompt_i1(self._task_description_str, self._function_to_evolve)
                self._sample_evaluate_register(prompt)
            except Exception as e:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

    def _init_population(self):
        # threads for sampling
        sampler_threads = [
            Thread(
                target=self._thread_init_population,
            ) for _ in range(self._num_samplers)
        ]
        for t in sampler_threads:
            t.start()
        for t in sampler_threads:
            t.join()

    def _do_sample(self):
        sampler_threads = [
            Thread(
                target=self._thread_do_evolutionary_operator,
            ) for _ in range(self._num_samplers)
        ]
        for t in sampler_threads:
            t.start()
        for t in sampler_threads:
            t.join()

    def run(self):
        if not self._resume_mode:
            # do init
            self._population = Population(pop_size=self._pop_size)
            self._init_population()
            while len([f for f in self._population if not np.isinf(np.array(f.score)).any()]) < self._selection_num:
                self._population._generation -= 1
                self._init_population()
        # do evolve
        self._do_sample()

        # finish
        if self._profiler is not None:
            self._profiler.finish()

        self._sampler.llm.close()
