# Module Name: HillClimb
# Last Revision: 2025/2/16
# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Reference:
#   - Rui Zhang, Fei Liu, Xi Lin, Zhenkun Wang, Zhichao Lu, and Qingfu Zhang. 
#       "Understanding the importance of evolutionary search in automated heuristic design with large language models." 
#       In International Conference on Parallel Problem Solving from Nature (PPSN), pp. 185-202. 2024.
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
import copy
import time
import traceback
from threading import Thread
from typing import Literal, Optional

from .profiler import HillClimbProfiler
from ...base import *


class HillClimb:
    def __init__(self,
                 llm: LLM,
                 evaluation: Evaluation,
                 profiler: HillClimbProfiler = None,
                 max_sample_nums: Optional[int] = 20,
                 num_samplers: int = 4,
                 num_evaluators: int = 4,
                 *,
                 resume_mode: bool = False,
                 debug_mode: bool = False,
                 multi_thread_or_process_eval: Literal['thread', 'process'] = 'thread',
                 **kwargs):
        """Hill Climbing Search.
        Args:
            llm             : an instance of 'llm4ad.base.LLM', which provides the way to query LLM.
            evaluation      : an instance of 'llm4ad.base.Evaluator', which defines the way to calculate the score of a generated function.
            profiler        : an instance of 'llm4ad.method.hillclimb.HillClimbProfiler'. If you do not want to use it, you can pass a 'None'.
            max_sample_nums : terminate after evaluating max_sample_nums functions (no matter the function is valid or not).
            num_samplers    : number of independent Samplers in the experiment.
            num_evaluators  : number of independent program Evaluators in the experiment.
            resume_mode     : in resume_mode, hillclimb will not evaluate the template_program, and will skip the init process. TODO: More detailed usage.
            debug_mode      : if set to True, we will print detailed information.
            multi_thread_or_process_eval: use 'concurrent.futures.ThreadPoolExecutor' or 'concurrent.futures.ProcessPoolExecutor' for the usage of
                multi-core CPU while evaluation. Please note that both settings can leverage multi-core CPU. As a result on my personal computer (Mac OS, Intel chip),
                setting this parameter to 'process' will faster than 'thread'. However, I do not sure if this happens on all platform so I set the default to 'thread'.
                Please note that there is one case that cannot utilize multi-core CPU: if you set 'safe_evaluate' argument in 'evaluator' to 'False',
                and you set this argument to 'thread'.
            **kwargs        : some args pass to 'llm4ad.base.SecureEvaluator'. Such as 'fork_proc'.
        """
        # arguments and keywords
        self._template_program_str = evaluation.template_program
        self._max_sample_nums = max_sample_nums
        self._num_samplers = num_samplers
        self._num_evaluators = num_evaluators
        self._debug_mode = debug_mode
        self._resume_mode = resume_mode

        # function to be evolved
        self._function_to_evolve: Function = TextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._function_to_evolve_name: str = self._function_to_evolve.name
        self._template_program: Program = TextFunctionProgramConverter.text_to_program(self._template_program_str)

        # sampler and evaluator
        self._sampler = SampleTrimmer(llm)
        llm.debug_mode = debug_mode
        self._evaluator = SecureEvaluator(evaluation, debug_mode=debug_mode, **kwargs)
        self._profiler = profiler

        # statistics
        self._tot_sample_nums = 0
        self._best_function_found = self._function_to_evolve  # set to the template function at the beginning

        # multi-thread executor for evaluation
        assert multi_thread_or_process_eval in ['thread', 'process']
        if multi_thread_or_process_eval == 'thread':
            self._evaluation_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._num_evaluators
            )
        else:
            self._evaluation_executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=self._num_evaluators
            )

        # threads for sampling
        self._sampler_threads = [
            Thread(target=self._sample_evaluate_register) for _ in range(self._num_samplers)
        ]

        # pass parameters to profiler
        if profiler is not None:
            self._profiler.record_parameters(llm, evaluation, self)  # ZL: necessary

    def _init(self):
        # evaluate the template program, make sure the score of which is not 'None'
        score, eval_time = self._evaluator.evaluate_program_record_time(program=self._template_program)
        if score is None:
            raise RuntimeError('The score of the template function must not be "None".')
        self._best_function_found.score = score

        # register the template program to the program database
        if self._profiler:
            self._function_to_evolve.score = score
            self._function_to_evolve.evaluate_time = eval_time
            self._profiler.register_function(self._function_to_evolve, program=str(self._template_program))

    def _get_prompt(self) -> str:
        template = TextFunctionProgramConverter.function_to_program(self._best_function_found, self._template_program)
        template.functions[0].name += '_v0'
        func_to_be_complete = copy.deepcopy(self._function_to_evolve)
        func_to_be_complete.name = self._function_to_evolve_name + '_v1'
        func_to_be_complete.docstring = f'    """Improved version of \'{self._function_to_evolve_name}_v0\'."""'
        func_to_be_complete.body = ''
        return '\n'.join([str(template), str(func_to_be_complete)])

    # def _sample_evaluate_register(self):
    #     while (self._max_sample_nums is None) or (self._tot_sample_nums < self._max_sample_nums):
    #         try:
    #             # do sample
    #             prompt_content = self._get_prompt()
    #             draw_sample_start = time.time()
    #             sampled_funcs = self._sampler.draw_samples([prompt_content])
    #             draw_sample_times = time.time() - draw_sample_start
    #             avg_time_for_each_sample = draw_sample_times / len(sampled_funcs)
    #
    #             # convert to program instance
    #             programs_to_be_eval = []
    #             for func in sampled_funcs:
    #                 program = SampleTrimmer.sample_to_program(func, self._template_program)
    #                 # if sample to program success
    #                 if program is not None:
    #                     programs_to_be_eval.append(program)
    #
    #             # submit tasks to the thread pool and evaluate
    #             futures = []
    #             for program in programs_to_be_eval:
    #                 future = self._evaluation_executor.submit(self._evaluator.evaluate_program_record_time, program)
    #                 futures.append(future)
    #             # get evaluate scores and evaluate times
    #             scores_times = [f.result() for f in futures]
    #             scores, times = [i[0] for i in scores_times], [i[1] for i in scores_times]
    #
    #             # update register to program database
    #             for program, score, eval_time in zip(programs_to_be_eval, scores, times):
    #                 # convert to Function instance
    #                 function = TextFunctionProgramConverter.program_to_function(program)
    #                 # check if the function has converted to Function instance successfully
    #                 if function is None:
    #                     continue
    #                 function.score = score
    #                 function.evaluate_time = eval_time
    #                 function.sample_time = avg_time_for_each_sample
    #                 # update best function found
    #                 if score is not None and score > self._best_function_found.score:
    #                     self._best_function_found = function
    #                 # register to profiler
    #                 if self._profiler:
    #                     self._profiler.register_function(function)
    #                 # update
    #                 self._tot_sample_nums += 1
    #         except KeyboardInterrupt:
    #             break
    #         except Exception as e:
    #             if self._debug_mode:
    #                 traceback.print_exc()
    #                 exit()
    #             continue
    #
    #     # shutdown evaluation_executor
    #     try:
    #         self._evaluation_executor.shutdown(cancel_futures=True)
    #     except:
    #         pass

    def _sample_evaluate_register(self):
        while (self._max_sample_nums is None) or (self._tot_sample_nums < self._max_sample_nums):
            try:
                # do sample
                prompt_content = self._get_prompt()
                draw_sample_start = time.time()
                sampled_func = self._sampler.draw_sample(prompt_content)
                draw_sample_time = time.time() - draw_sample_start

                # convert samples to program instances
                program_to_be_eval = SampleTrimmer.sample_to_program(sampled_func, self._template_program)
                if program_to_be_eval is None:
                    continue

                # submit tasks to the thread pool and evaluate
                future = self._evaluation_executor.submit(
                    self._evaluator.evaluate_program_record_time, program_to_be_eval
                )

                # get evaluate scores and evaluate times
                score, eval_time = future.result()

                # convert to Function instance
                function = TextFunctionProgramConverter.program_to_function(program_to_be_eval)

                # check if the function has converted to Function instance successfully
                if function is None:
                    continue
                function.score = score
                function.evaluate_time = eval_time
                function.sample_time = draw_sample_time

                # update best function found
                if score is not None and score > self._best_function_found.score:
                    self._best_function_found = function

                # register to profiler
                if self._profiler:
                    self._profiler.register_function(function, program=str(program_to_be_eval))

                # update
                self._tot_sample_nums += 1

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

    def run(self):
        if not self._resume_mode:
            # do init
            self._init()

        # start sampling using multiple threads
        for t in self._sampler_threads:
            t.start()

        # join all threads to the main thread
        for t in self._sampler_threads:
            t.join()

        if self._profiler is not None:
            self._profiler.finish()

        self._sampler.llm.close()