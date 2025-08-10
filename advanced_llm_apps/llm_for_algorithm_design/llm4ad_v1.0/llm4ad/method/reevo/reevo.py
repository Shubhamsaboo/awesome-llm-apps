# Module Name: ReEvo
# Last Revision: 2025/2/16
# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Reference:
#
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
import time
import traceback
from threading import Thread
from typing import Optional, Literal

from torch.utils.data import Sampler

from .population import Population
from .profiler import ReEvoProfiler
from .prompt import ReEvoPrompt
from ...base import (
    Evaluation, LLM, Function, Program, TextFunctionProgramConverter, SecureEvaluator, SampleTrimmer
)
from ...tools.profiler import ProfilerBase


class ReEvo:
    def __init__(self,
                 llm: LLM,
                 evaluation: Evaluation,
                 profiler: ProfilerBase = None,
                 max_sample_nums: Optional[int] = 100,
                 pop_size: Optional[int] = 20,
                 mutation_rate: float = 0.5,
                 num_samplers: int = 1,
                 num_evaluators: int = 1,
                 *,
                 resume_mode: bool = False,
                 debug_mode: bool = False,
                 multi_thread_or_process_eval: Literal['thread', 'process'] = 'thread',
                 **kwargs):
        """Reflective Evolution.
        Args:
            llm             : an instance of 'llm4ad.base.LLM', which provides the way to query LLM.
            evaluation      : an instance of 'llm4ad.base.Evaluator', which defines the way to calculate the score of a generated function.
            profiler        : an instance of 'llm4ad.method.reevo.ReEvoProfiler'. If you do not want to use it, you can pass a 'None'.
            max_generations : terminate after evolving 'max_generations' generations or reach 'max_sample_nums',
                              pass 'None' to disable this termination condition.
            max_sample_nums : terminate after evaluating max_sample_nums functions (no matter the function is valid or not) or reach 'max_generations',
                              pass 'None' to disable this termination condition.
            pop_size        : population size, if set to 'None', EoH will automatically adjust this parameter.
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
        self._max_sample_nums = max_sample_nums
        self._pop_size = pop_size
        self._mutation_rate = mutation_rate

        # samplers and evaluators
        self._num_samplers = num_samplers
        self._num_evaluators = num_evaluators
        self._resume_mode = resume_mode
        self._debug_mode = debug_mode
        llm.debug_mode = debug_mode
        self._multi_thread_or_process_eval = multi_thread_or_process_eval
        self._MAX_SHORT_TERM_REFLECTION_PROMPT = 5

        # function to be evolved
        self._function_to_evolve: Function = TextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._function_to_evolve_name: str = self._function_to_evolve.name
        self._template_program: Program = TextFunctionProgramConverter.text_to_program(self._template_program_str)

        # population, sampler, and evaluator
        self._population = Population(pop_size=self._pop_size)
        self._sampler = SampleTrimmer(llm)
        self._evaluator = SecureEvaluator(evaluation, debug_mode=debug_mode, **kwargs)
        self._profiler = profiler

        # statistics
        self._tot_sample_nums = 0

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
            self._profiler.record_parameters(llm, evaluation, self)  # ZL: necessary

    def _sample_evaluate_register(self, prompt):
        """Perform following steps:
        1. Sample an algorithm using the given prompt.
        2. Evaluate it by submitting to the process/thread pool, and get the results.
        3. Add the function to the population and register it to the profiler.
        """
        sample_start = time.time()
        func = self._sampler.draw_sample(prompt)
        func = SampleTrimmer.sample_to_function(func, self._template_program)
        sample_time = time.time() - sample_start
        if func is None:
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
        # register to profiler
        func.score = score
        func.evaluate_time = eval_time
        func.sample_time = sample_time
        if self._profiler is not None:
            self._profiler.register_function(func, program=str(program))
            if isinstance(self._profiler, ReEvoProfiler):
                self._profiler.register_population(self._population)
        self._tot_sample_nums += 1

        # register to the population
        self._population.register_function(func)

    def _iteratively_ga_evolve(self):
        short_term_reflection_prompts = []
        long_term_reflection_prompts = []
        crx_samples_generated_by_cur_thread = 0

        while self._tot_sample_nums < self._max_sample_nums:
            try:
                # short term reflection
                indivs = [self._population.selection() for _ in range(2)]
                short_term_reflection_prompt = ReEvoPrompt.get_short_term_reflection_prompt(self._task_description_str,
                                                                                            indivs)

                if self._debug_mode:
                    print(f'--------------------------------------------------------------------')
                    print(f'Short Term Reflection Prompt-1: \n{short_term_reflection_prompt}')
                    print(f'--------------------------------------------------------------------\n\n')

                short_term_reflection_prompt = self._sampler.llm.draw_sample(short_term_reflection_prompt)
                short_term_reflection_prompts.append(short_term_reflection_prompt)

                if self._debug_mode:
                    print(f'--------------------------------------------------------------------')
                    print(f'Short Term Reflection Prompt-2: \n{short_term_reflection_prompt}')
                    print(f'--------------------------------------------------------------------\n\n')

                # crossover
                crx_prompt = ReEvoPrompt.get_crossover_prompt(self._task_description_str, short_term_reflection_prompt,
                                                              indivs)

                if self._debug_mode:
                    print(f'--------------------------------------------------------------------')
                    print(f'Crossover Prompt: \n{crx_prompt}')
                    print(f'--------------------------------------------------------------------\n\n')

                self._sample_evaluate_register(crx_prompt)
                crx_samples_generated_by_cur_thread += 1
                if self._tot_sample_nums >= self._max_sample_nums:
                    break

                # assume that current thread has generated a population of algorithms
                if crx_samples_generated_by_cur_thread > 0 and crx_samples_generated_by_cur_thread % self._pop_size == 0:
                    # long term reflection
                    long_term_reflection_prompt = ReEvoPrompt.get_long_term_reflection_prompt(
                        self._task_description_str,
                        long_term_reflection_prompts[-1] if long_term_reflection_prompts else '',
                        short_term_reflection_prompts[-self._MAX_SHORT_TERM_REFLECTION_PROMPT:],
                    )

                    if self._debug_mode:
                        print(f'--------------------------------------------------------------------')
                        print(f'Long Term Reflection Prompt-1: \n{long_term_reflection_prompt}')
                        print(f'--------------------------------------------------------------------\n\n')

                    long_term_reflection_prompt = self._sampler.llm.draw_sample(long_term_reflection_prompt)
                    long_term_reflection_prompts.append(long_term_reflection_prompt)

                    if self._debug_mode:
                        print(f'--------------------------------------------------------------------')
                        print(f'Long Term Reflection Prompt-2: \n{long_term_reflection_prompt}')
                        print(f'--------------------------------------------------------------------\n\n')

                    # mutation
                    for _ in range(int(self._mutation_rate * self._pop_size)):
                        func = self._population.elite_function
                        mutation_prompt = ReEvoPrompt.get_elist_mutation_prompt(self._task_description_str,
                                                                                long_term_reflection_prompt, func)

                        if self._debug_mode:
                            print(f'--------------------------------------------------------------------')
                            print(f'Elite mutation: \n{mutation_prompt}')
                            print(f'--------------------------------------------------------------------\n\n')

                        self._sample_evaluate_register(mutation_prompt)

                    if self._tot_sample_nums >= self._max_sample_nums:
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

    def _iteratively_init_population(self):
        """Let a thread repeat {sample -> evaluate -> register to population}
        to initialize a population.
        """
        while self._population.generation == 0:
            try:
                # get a new func using i1
                prompt = ReEvoPrompt.get_pop_init_prompt(self._task_description_str, self._function_to_evolve)
                if self._debug_mode:
                    print(f'Init Prompt: {prompt}')
                self._sample_evaluate_register(prompt)
            except Exception:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

    def _multi_threaded_sampling(self, fn: callable, *args, **kwargs):
        """Execute `fn` using multithreading.
        In EoH, `fn` can be `self._iteratively_init_population` or `self._iteratively_use_eoh_operator`.
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
            self._multi_threaded_sampling(self._iteratively_init_population)

        # evolutionary search
        self._multi_threaded_sampling(self._iteratively_ga_evolve)

        # finish
        if self._profiler is not None:
            self._profiler.finish()

        self._sampler.llm.close()
