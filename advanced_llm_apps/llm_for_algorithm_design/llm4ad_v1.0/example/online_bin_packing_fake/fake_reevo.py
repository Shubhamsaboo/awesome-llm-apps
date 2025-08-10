from __future__ import annotations

import pickle
import random
from typing import Any
import sys

from llm4ad.tools.llm.llm_api_https import HttpsApi

sys.path.append('../../../')  # This is for finding all the modules

from llm4ad.task.optimization.online_bin_packing import OBPEvaluation
from llm4ad.base import LLM
from llm4ad.method.reevo.reevo import ReEvo, ReEvoProfiler


class FakeLLM(LLM):
    """We select random functions from rand_function.pkl
    This sampler can help you debug your method even if you don't have an LLM API / deployed local LLM.
    """

    def __init__(self):
        super().__init__()
        with open('_data/rand_function.pkl', 'rb') as f:
            self._functions = pickle.load(f)

    def draw_sample(self, prompt: str | Any, *args, **kwargs) -> str:
        fake_thought = '{This is a fake thought for the code}\n'
        rand_func = random.choice(self._functions)
        return fake_thought + rand_func


llm = FakeLLM()

if __name__ == '__main__':
    # llm = FakeLLM()
    task = OBPEvaluation()
    method = ReEvo(
        llm=llm,
        profiler=ReEvoProfiler(log_dir='logs/reevo', log_style='complex'),
        evaluation=task,
        max_sample_nums=20,
        pop_size=2,
        num_samplers=1,
        num_evaluators=1,
        debug_mode=True,
    )
    method._evaluator._debug_mode = False
    method.run()
