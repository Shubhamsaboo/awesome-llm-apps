from __future__ import annotations

import pickle
import random
from typing import Any
import sys

sys.path.append('../../../')  # This is for finding all the modules

from llm4ad.task.optimization.online_bin_packing import OBPEvaluation
from llm4ad.base import LLM
from llm4ad.method.eoh import EoH, EoHProfiler, EoHTensorboardProfiler
from llm4ad.tools.profiler import ProfilerBase, TensorboardProfiler


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


if __name__ == '__main__':
    llm = FakeLLM()
    task = OBPEvaluation()
    method = EoH(
        llm=FakeLLM(),
        profiler=EoHTensorboardProfiler(log_dir='logs/eoh', log_style='simple'),
        evaluation=task,
        max_sample_nums=20,
        max_generations=5,
        pop_size=2,
        num_samplers=1,
        num_evaluators=1,
    )
    method.run()
