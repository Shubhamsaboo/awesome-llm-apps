from __future__ import annotations

import copy
from typing import List, Dict

from ...base import *


class ReEvoPrompt:

    @classmethod
    def get_pop_init_prompt(cls, task_prompt: str, template_function: Function) -> str:
        sys = ('You are an expert in the domain of optimization heuristics. '
               'Your task is to design heuristics that can effectively solve optimization problems. '
               'Your response outputs Python code and nothing else. Format your code as a Python code string: "```python ...```"')
        template_function = copy.deepcopy(template_function)
        func_name = template_function.name
        template_function.name = f'{template_function.name}_v1'
        prompt = f'''{task_prompt}  
{template_function}  
Improve `{func_name}_v1` to give `{func_name}_v2`. Output code only and enclose your code with Python code block: ```python ...```.  
'''
        return '\n'.join([sys, prompt])

    @classmethod
    def get_short_term_reflection_prompt(cls, task_prompt: str, indivs: List[Function]) -> str:
        sys = 'You are an expert in the domain of optimization heuristics. Your task is to give hints to design better heuristics.'
        assert len(indivs) == 2
        indivs = copy.deepcopy(indivs)
        indivs.sort(key=lambda function: function.score)
        prompt = f'''Below are two {indivs[0].name} functions for {task_prompt}.
You are provided with two code versions below, where the second version performs better than the first one.  
[Worse code] 
{indivs[0]}  
[Better code] 
{indivs[1]}
You respond with some hints for designing better heuristics, based on the two code versions and using less than 20 words.'''
        return '\n'.join([sys, prompt])

    @classmethod
    def get_crossover_prompt(cls, task_prompt: str, short_term_reflection_prompt: str, indivs: List[Function], ) -> str:
        sys = ('You are an expert in the domain of optimization heuristics. '
               'Your task is to design heuristics that can effectively solve optimization problems. '
               'Your response outputs Python code and nothing else. Format your code as a Python code string: "```python ...```"')
        indivs = copy.deepcopy(indivs)
        indivs.sort(key=lambda function: function.score)
        func_name = indivs[0].name
        indivs[0].name = f'{indivs[0].name}_v0'
        indivs[1].name = f'{indivs[1].name}_v1'
        prompt = f'''{task_prompt}  
[Worse code] 
{indivs[0]}  
[Better code] 
{indivs[1]}
[Reflection] 
{short_term_reflection_prompt}  
[Improved code]
Please write an improved function `{func_name}_v2`, according to the reflection. Output code only and enclose your code with Python code block: ```python ... ```.
        '''
        return '\n'.join([sys, prompt])

    @classmethod
    def get_long_term_reflection_prompt(cls, task_prompt: str, prior_long_term_reflection: str, new_short_term_reflections: List[str]) -> str:
        sys = 'You are an expert in the domain of optimization heuristics. Your task is to give hints to design better heuristics.'
        new_short_term_reflections = '\n'.join(new_short_term_reflections)
        prompt = f'''Below is your prior long-term reflection on designing heuristics for {task_prompt}:
{prior_long_term_reflection}
Below are some newly gained insights:
{new_short_term_reflections} 
Write constructive hints for designing better heuristics, based on prior reflections and new insights and using less than 50 words.'''
        return '\n'.join([sys, prompt])

    @classmethod
    def get_elist_mutation_prompt(cls, task_prompt: str, long_term_reflection_prompt: str, elite_function: Function) -> str:
        sys = ('You are an expert in the domain of optimization heuristics. '
               'Your task is to design heuristics that can effectively solve optimization problems. '
               'Your response outputs Python code and nothing else. Format your code as a Python code string: "```python ...```"')
        elite_function = copy.deepcopy(elite_function)
        func_name = elite_function.name
        elite_function.name = f'{elite_function.name}_v1'
        prompt = f'''{task_prompt}
[Prior reflection] 
{long_term_reflection_prompt}  
[Code] 
{elite_function} 
[Improved code]
Please write a mutated function `{func_name}_v2`, according to the reflection. Output code only and enclose your code with Python code block: ```python ...```.
        '''
        return '\n'.join([sys, prompt])
