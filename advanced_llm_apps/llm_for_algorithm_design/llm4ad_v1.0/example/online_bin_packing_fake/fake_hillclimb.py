from __future__ import annotations

import pickle
import random
from typing import Any
import sys

sys.path.append('../../../')  # This is for finding all the modules

from llm4ad.task.optimization.online_bin_packing import OBPEvaluation
from llm4ad.base import LLM
from llm4ad.method.hillclimb import HillClimb
from llm4ad.tools.profiler import ProfilerBase


class FakeLLM(LLM):
    """We select random functions from rand_function.pkl
    This sampler can help you debug your method even if you don't have an LLM API / deployed local LLM.
    """

    def __init__(self):
        super().__init__()
        with open('_data/rand_function.pkl', 'rb') as f:
            self._functions = pickle.load(f)

    def draw_sample(self, prompt: str | Any, *args, **kwargs) -> str:
        return random.choice(self._functions)


if __name__ == '__main__':
    llm = FakeLLM()
    task = OBPEvaluation()
    hillclimb = HillClimb(
        llm=llm,
        profiler=ProfilerBase(log_dir='logs/hillclimb', log_style='simple'),
        evaluation=task,
        max_sample_nums=10,
        num_samplers=1,
        num_evaluators=1,
    )
    hillclimb.run()
