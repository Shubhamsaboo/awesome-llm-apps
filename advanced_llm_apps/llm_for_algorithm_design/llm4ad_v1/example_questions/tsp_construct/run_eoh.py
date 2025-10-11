from __future__ import annotations
import os
import sys
from pathlib import Path

# Derive project root and ensure it's on sys.path before any llm4ad imports
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from llm4ad.task.optimization.tsp_construct import TSPEvaluation
from llm4ad.tools.llm.llm_api_https import HttpsApi
from llm4ad.tools.profiler import ProfilerBase
from llm4ad.method.eoh import EoH

from dotenv import load_dotenv

def main():
    """
    Run EoH method on TSP problem
    """
    llm = HttpsApi(host='xxx',  # your host endpoint, e.g., 'api.openai.com', 'api.deepseek.com'
                   key=os.getenv("LLM4AD_API_KEY"),  # your key, e.g., 'sk-abcdefghijklmn'
                   model='xxx',  # your llm, e.g., 'gpt-3.5-turbo'
                   timeout=60)

    task = TSPEvaluation()

    method = EoH(llm=llm,
                 profiler=ProfilerBase(log_dir='logs', log_style='complex'),
                 evaluation=task,
                 max_sample_nums=20,
                 max_generations=5,
                 pop_size=2,
                 num_samplers=1,
                 num_evaluators=1)

    method.run()


if __name__ == '__main__':
    main()
