from __future__ import annotations

import sys

sys.path.append('../../../')  # This is for finding all the modules

from llm4ad.task.optimization.online_bin_packing import OBPEvaluation
from llm4ad.tools.llm.llm_api_https import HttpsApi
from llm4ad.method.funsearch import FunSearch
from llm4ad.tools.profiler import ProfilerBase

if __name__ == '__main__':
    llm = HttpsApi(host='xxx',  # your host endpoint, e.g., 'api.openai.com', 'api.deepseek.com'
                   key='sk-xxx',  # your key, e.g., 'sk-abcdefghijklmn'
                   model='xxx',  # your llm, e.g., 'gpt-3.5-turbo'
                   timeout=60)

    task = OBPEvaluation()

    method = FunSearch(
        llm=llm,
        profiler=ProfilerBase(log_dir='logs/funsearch', log_style='simple'),
        evaluation=task,
        max_sample_nums=20,
        num_samplers=1,
        num_evaluators=1,
    )

    method.run()
