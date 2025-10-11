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
