# Module Name: MCTS_AHD
# Last Revision: 2025/7/22
# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Reference:
#   - Zheng, Z., Xie, Z., Wang, Z., & Hooi, B. (2025). Monte carlo tree search for
#       comprehensive exploration in llm-based automatic heuristic design. (ICML). 2024.
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
import heapq
import concurrent.futures
import copy
import random
import time
import traceback
from threading import Thread
from typing import Optional, Literal

from .population import Population
from .mcts import MCTS, MCTSNode
from .profiler import MAProfiler
from .prompt import MAPrompt
from .sampler import MASampler
from ...base import (
    Evaluation, LLM, Function, Program, TextFunctionProgramConverter, SecureEvaluator
)
from ...tools.profiler import ProfilerBase


class MCTS_AHD:
    def __init__(self,
                 llm: LLM,
                 evaluation: Evaluation,
                 profiler: ProfilerBase = None,
                 max_sample_nums: Optional[int] = 100,
                 init_size: Optional[float] = 4,
                 pop_size: Optional[int] = 10,
                 selection_num: int = 2,
                 num_samplers: int = 1,
                 num_evaluators: int = 1,
                 alpha: float = 0.5,
                 lambda_0: float = 0.1,
                 *,
                 resume_mode: bool = False,
                 debug_mode: bool = False,
                 multi_thread_or_process_eval: Literal['thread', 'process'] = 'thread',
                 **kwargs):
        """Evolutionary of Heuristics.
        Args:
            llm             : an instance of 'llm4ad.base.LLM', which provides the way to query LLM.
            evaluation      : an instance of 'llm4ad.base.Evaluator', which defines the way to calculate the score of a generated function.
            profiler        : an instance of 'llm4ad.method.eoh.EoHProfiler'. If you do not want to use it, you can pass a 'None'.
                              pass 'None' to disable this termination condition.
            max_sample_nums : terminate after evaluating max_sample_nums functions (no matter the function is valid or not) or reach 'max_generations',
                              pass 'None' to disable this termination condition.
            init_size       : population size, if set to 'None', EoH will automatically adjust this parameter.
            pop_size        : population size, if set to 'None', EoH will automatically adjust this parameter.
            selection_num   : number of selected individuals while crossover.
            alpha           : a parameter for the UCT formula, which is used to balance exploration and exploitation.
            lambda_0        : a parameter for the UCT formula, which is used to balance exploration and exploitation.
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
        self._max_sample_nums = max_sample_nums
        self.lambda_0 = lambda_0
        self.alpha = alpha
        self._init_pop_size = init_size
        self._pop_size = pop_size
        self._selection_num = selection_num

        # samplers and evaluators
        self._num_samplers = num_samplers
        self._num_evaluators = num_evaluators
        self._resume_mode = resume_mode
        self._debug_mode = debug_mode
        llm.debug_mode = debug_mode
        self._multi_thread_or_process_eval = multi_thread_or_process_eval

        # function to be evolved
        self._function_to_evolve: Function = TextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._function_to_evolve_name: str = self._function_to_evolve.name
        self._template_program: Program = TextFunctionProgramConverter.text_to_program(self._template_program_str)

        # adjust population size
        self._adjust_pop_size()

        # population, sampler, and evaluator
        self._population = Population(init_pop_size=init_size, pop_size=self._pop_size)
        self._sampler = MASampler(llm, self._template_program_str)
        self._evaluator = SecureEvaluator(evaluation, debug_mode=debug_mode, **kwargs)
        self._profiler = profiler

        # statistics
        self._tot_sample_nums = 0

        # reset _initial_sample_nums_max
        self._initial_sample_nums_max = min(
            self._max_sample_nums,
            10 * self._init_pop_size
        )

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

    def _adjust_pop_size(self):
        # adjust population size
        if self._max_sample_nums >= 10000:
            if self._pop_size is None:
                self._pop_size = 40
            elif abs(self._pop_size - 40) > 20:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 40.')
        elif self._max_sample_nums >= 1000:
            if self._pop_size is None:
                self._pop_size = 20
            elif abs(self._pop_size - 20) > 10:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 20.')
        elif self._max_sample_nums >= 200:
            if self._pop_size is None:
                self._pop_size = 10
            elif abs(self._pop_size - 10) > 5:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 10.')
        else:
            if self._pop_size is None:
                self._pop_size = 5
            elif abs(self._pop_size - 5) > 5:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 5.')

    def _sample_evaluate_register(self, prompt, func_only=False):
        """Perform following steps:
        1. Sample an algorithm using the given prompt.
        2. Evaluate it by submitting to the process/thread pool, and get the results.
        3. Add the function to the population and register it to the profiler.
        """
        sample_start = time.time()
        thought, func = self._sampler.get_thought_and_function(self._task_description_str, prompt)
        sample_time = time.time() - sample_start
        if thought is None or func is None:
            return False
        # convert to Program instance
        program = TextFunctionProgramConverter.function_to_program(func, self._template_program)
        if program is None:
            return False
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
            self._profiler.register_function(func, program=str(program))
            if isinstance(self._profiler, MAProfiler):
                self._profiler.register_population(self._population)
            self._tot_sample_nums += 1
        if func_only:
            return func
        if func.score is None:
            return False
        # register to the population
        self._population.register_function(func)

        return True

    def _continue_loop(self) -> bool:
        if self._max_sample_nums is None:
            return True
        else:
            return self._tot_sample_nums < self._max_sample_nums

    def check_duplicate(self, population, code):
        for ind in population:
            if code == ind.code:
                return True
        return False

    def check_duplicate_obj(self, population, code):
        for ind in population:
            if code == ind.individual.score:
                return True
        return False

    def population_management_s1(self, pop_input, size):
        unique_pop = []
        unique_algorithms = []
        for individual in pop_input:
            if str(individual) not in unique_algorithms:
                unique_pop.append(individual)
                unique_algorithms.append(str(individual))
        # Delete the worst individual
        # pop_new = heapq.nsmallest(size, pop, key=lambda x: x['objective'])
        pop_new = heapq.nlargest(size, unique_pop, key=lambda x: x.score)
        return pop_new

    def expand(self, mcts: MCTS, node_set, cur_node: MCTSNode, option: str):
        is_valid_func = True
        if option == 's1':
            path_set = []
            now = copy.deepcopy(cur_node)
            while now.algorithm != "Root":
                path_set.append(now.individual)
                now = copy.deepcopy(now.parent)
            path_set = self.population_management_s1(path_set, len(path_set))
            if len(path_set) == 1:
                return node_set

            i = 0
            while i < 3:
                prompt = MAPrompt.get_prompt_s1(self._task_description_str, path_set, self._function_to_evolve)
                func = self._sample_evaluate_register(prompt, func_only=True)
                if func is False:
                    is_valid_func = False
                    i += 1
                    continue
                is_valid_func = (func.score is not None) and not self.check_duplicate(node_set, str(func))
                if is_valid_func is False:
                    i += 1
                    continue
                else:
                    break

        elif option == 'e1':
            indivs = [copy.deepcopy(children.subtree[random.choices(range(len(children.subtree)), k=1)[0]].individual)
                      for
                      children in mcts.root.children]
            prompt = MAPrompt.get_prompt_e1(self._task_description_str, indivs, self._function_to_evolve)
            func = self._sample_evaluate_register(prompt, func_only=True)
            if func is False:
                is_valid_func = False
            else:
                is_valid_func = (func.score is not None)

        elif option == 'e2':
            i = 0
            while i < 3:
                now_indiv = None
                while True:
                    now_indiv = self._population.selection()
                    if now_indiv != cur_node.individual:
                        break
                prompt = MAPrompt.get_prompt_e2(self._task_description_str, [now_indiv, cur_node.individual],
                                                self._function_to_evolve)
                func = self._sample_evaluate_register(prompt, func_only=True)
                if func is False:
                    is_valid_func = False
                    i += 1
                    continue
                is_valid_func = (func.score is not None) and not self.check_duplicate(node_set, str(func))
                if is_valid_func is False:
                    i += 1
                    continue
                else:
                    break

        elif option == 'm1':
            i = 0
            while i < 3:
                prompt = MAPrompt.get_prompt_m1(self._task_description_str, cur_node.individual,
                                                self._function_to_evolve)
                func = self._sample_evaluate_register(prompt, func_only=True)
                if func is False:
                    is_valid_func = False
                    i += 1
                    continue
                is_valid_func = (func.score is not None) and not self.check_duplicate(node_set, str(func))
                if is_valid_func is False:
                    i += 1
                    continue
                else:
                    break

        elif option == 'm2':
            i = 0
            while i < 3:
                prompt = MAPrompt.get_prompt_m2(self._task_description_str, cur_node.individual,
                                                self._function_to_evolve)
                func = self._sample_evaluate_register(prompt, func_only=True)
                if func is False:
                    is_valid_func = False
                    i += 1
                    continue
                is_valid_func = (func.score is not None) and not self.check_duplicate(node_set, str(func))
                if is_valid_func is False:
                    i += 1
                    continue
                else:
                    break

        else:
            assert False, 'Invalid option!'

        if not is_valid_func:
            print(f"Timeout emerge, no expanding with action {option}.")
            return node_set

        if option != 'e1':
            print(
                f"Action: {option}, Father Obj: {cur_node.raw_info.score}, Now Obj: {func.score}, Depth: {cur_node.depth + 1}")
        else:
            if self.check_duplicate_obj(node_set, func.score):
                print(f"Duplicated e1, no action, Father is Root, Abandon Obj: {func.score}")
            else:
                print(f"Action: {option}, Father is Root, Now Obj: {func.score}")

        if is_valid_func and func.score != float('-inf'):
            self._population.register_function(func)
            now_node = MCTSNode(func.algorithm, str(func), -1 * func.score, individual=func,
                                parent=cur_node, depth=1, visit=1, Q=func.score, raw_info=func)
            if option == 'e1':
                now_node.subtree.append(now_node)
            cur_node.add_child(now_node)
            mcts.backpropagate(now_node)
            node_set.append(now_node)
        return node_set

    def _iteratively_init_population_root(self):
        """Let a thread repeat {sample -> evaluate -> register to population}
        to initialize a population.
        """
        while len(self._population.population) < self._init_pop_size:
            try:
                # get a new func using e1
                prompt = MAPrompt.get_prompt_e1(self._task_description_str, self._population.population,
                                                self._function_to_evolve)
                self._sample_evaluate_register(prompt)
                self._population.survival()

                if self._tot_sample_nums >= self._initial_sample_nums_max:
                    # print(f'Warning: Initialization not accomplished in {self._initial_sample_nums_max} samples !!!')
                    print(
                        f'Note: During initialization, EoH gets {len(self._population) + len(self._population._next_gen_pop)} algorithms '
                        f'after {self._initial_sample_nums_max} trails.')
                    break
            except Exception:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

    def _init_one_solution(self):
        while len(self._population.next_gen_pop) == 0:
            try:
                # get a new func using i1
                prompt = MAPrompt.get_prompt_i1(self._task_description_str, self._function_to_evolve)
                self._sample_evaluate_register(prompt)
            except Exception:
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue

    def _multi_threaded_sampling(self, fn: callable, *args, **kwargs):
        """Execute `fn` using multithreading.
        In MCTS_MA, `fn` can be `self._iteratively_use_eoh_operator`.
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
        mcts = MCTS('Root', self.alpha, self.lambda_0)
        # do initialization

        # 1. first generate one solution as initialization
        self._init_one_solution()
        self._population.survival()

        # 2. expand root
        self._iteratively_init_population_root()

        # 3. update mcts
        for indiv in self._population.population:
            now_node = MCTSNode(indiv.algorithm, str(indiv), -1 * indiv.score, individual=indiv,
                                parent=mcts.root,
                                depth=1, visit=1, Q=indiv.score, raw_info=indiv)
            mcts.root.add_child(now_node)
            mcts.backpropagate(now_node)
            now_node.subtree.append(now_node)

        # terminate searching if
        if len(self._population) < self._selection_num:
            print(
                f'The search is terminated since MCTS_AHD unable to obtain {self._selection_num} feasible algorithms during initialization. '
                f'Please increase the `initial_sample_nums_max` argument (currently {self._initial_sample_nums_max}). '
                f'Please also check your evaluation implementation and LLM implementation.')
            return

        # evolutionary search
        n_op = ['e1', 'e2', 'm1', 'm2', 's1']
        op_weights = [0, 1, 2, 2, 1]
        while self._continue_loop():
            node_set = []
            print(f"Current performances of MCTS nodes: {mcts.rank_list}")
            print(
                f"Current number of MCTS nodes in the subtree of each child of the root: {[len(node.subtree) for node in mcts.root.children]}")
            cur_node = mcts.root
            while len(cur_node.children) > 0 and cur_node.depth < mcts.max_depth:
                uct_scores = [mcts.uct(node, max(1 - self._tot_sample_nums / self._max_sample_nums, 0)) for node in
                              cur_node.children]
                selected_pair_idx = uct_scores.index(max(uct_scores))
                if int((cur_node.visits) ** mcts.alpha) > len(cur_node.children):
                    if cur_node == mcts.root:
                        op = 'e1'
                        self.expand(mcts, mcts.root.children, cur_node, op)
                    else:
                        # i = random.randint(1, n_op - 1)
                        op = 'e2'
                        self.expand(mcts, cur_node.children, cur_node, op)
                cur_node = cur_node.children[selected_pair_idx]
            for i in range(len(n_op)):
                op = n_op[i]
                print(f"Iter: {self._tot_sample_nums}/{self._max_sample_nums} OP: {op}", end="|")
                op_w = op_weights[i]
                for j in range(op_w):
                    node_set = self.expand(mcts, node_set, cur_node, op)
            self._population.survival()

        # finish
        if self._profiler is not None:
            self._profiler.finish()

        self._sampler.llm.close()
