### Test Only ###
# Set system path

import sys

sys.path.append('../../../')  # This is for finding all the modules

from llm4ad.task.optimization.cvrp_construct import CVRPEvaluation
from llm4ad.tools.llm.llm_api_https import HttpsApi
from llm4ad.method.eoh import EoH, EoHProfiler


def main():
    llm = HttpsApi(host='xxx',  # your host endpoint, e.g., 'api.openai.com', 'api.deepseek.com'
                   key='sk-xxx',  # your key, e.g., 'sk-abcdefghijklmn'
                   model='xxx',  # your llm, e.g., 'gpt-3.5-turbo'
                   timeout=60)

    task = CVRPEvaluation()

    method = EoH(llm=llm,
                 profiler=EoHProfiler(log_dir='logs', log_style='complex'),
                 evaluation=task,
                 max_sample_nums=100,
                 max_generations=10,
                 pop_size=20,
                 num_samplers=4,
                 num_evaluators=4)

    method.run()


if __name__ == '__main__':
    main()
