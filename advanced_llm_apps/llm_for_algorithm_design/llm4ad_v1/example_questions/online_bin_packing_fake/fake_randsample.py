from __future__ import annotations
import pickle
import random
import sys
from pathlib import Path
from typing import Any

# Derive project root and ensure it's on sys.path before any llm4ad imports
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from llm4ad.task.optimization.online_bin_packing import OBPEvaluation
from llm4ad.base import LLM
from llm4ad.method.randsample import RandSample
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
    rand_sample = RandSample(
        llm=llm,
        profiler=ProfilerBase(log_dir='logs/randomsample', log_style='simple'),
        evaluation=task,
        max_sample_nums=10,
        num_samplers=1,
        num_evaluators=1,
    )
    rand_sample.run()
