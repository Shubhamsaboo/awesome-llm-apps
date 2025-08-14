import sys

sys.path.append('../../')  # This is for finding all the modules

from evaluation import CirclePackingEvaluation
from llm4ad.tools.llm.llm_api_https import HttpsApi
from llm4ad.method.eoh import EoH,EoHProfiler
from llm4ad.tools.profiler import ProfilerBase


def main():
    llm = HttpsApi(host='api.bltcy.ai',  # your host endpoint, e.g., 'api.openai.com', 'api.deepseek.com'
                   key='sk-bxkYIPpRbqTWS0cGB01009DfE8F94c2f8a26082248Bf7e98',  # your key, e.g., 'sk-abcdefghijklmn'
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
