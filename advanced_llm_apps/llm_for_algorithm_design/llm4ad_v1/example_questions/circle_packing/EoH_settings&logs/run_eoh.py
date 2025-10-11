from __future__ import annotations
import os
import sys
from pathlib import Path

# Derive project root and ensure it's on sys.path before any llm4ad imports
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from evaluation import CirclePackingEvaluation
from llm4ad.tools.llm.llm_api_https import HttpsApi
from llm4ad.method.eoh import EoH,EoHProfiler

# from dotenv import load_dotenv

def main():
    """
    Run EoH on CirclePackingEvaluation
    """
    llm = HttpsApi(host='api.bltcy.ai',  # your host endpoint, e.g., 'api.openai.com', 'api.deepseek.com'
                   key=os.getenv("LLM4AD_API_KEY"),  # your key
                   model='deepseek-v3',  # your llm, e.g., 'gpt-3.5-turbo'
                   timeout=120)

    task = CirclePackingEvaluation(timeout_seconds=1200)  # local

    method = EoH(llm=llm,
                 profiler=EoHProfiler(log_dir='logs/eohseed', log_style='simple'),
                 evaluation=task,
                 max_sample_nums=15000,
                 max_generations=10000,
                 pop_size=32,
                 num_samplers=32,
                 num_evaluators=32,
                 debug_mode=False)

    method.run()


if __name__ == '__main__':
    main()
