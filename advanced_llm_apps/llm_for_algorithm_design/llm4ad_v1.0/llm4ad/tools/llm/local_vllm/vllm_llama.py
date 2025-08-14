import gc
import random
import traceback
from argparse import ArgumentParser
from typing import List, Dict

import torch
from flask import Flask, request, jsonify
from flask_cors import CORS

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
import os

default_model_path_path = 'Llama-3.2-1B-Instruct'
default_toknz_path_path = 'Llama-3.2-1B-Instruct'

# arguments
parser = ArgumentParser()
parser.add_argument('--d', nargs='+', default=['0'])
parser.add_argument('--path', type=str, default=default_model_path_path)
parser.add_argument('--tknz_path', type=str, default=default_toknz_path_path)
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=22001)
parser.add_argument('--max_model_len', type=int, default=16384)
parser.add_argument('--gpu_memory_utilization', type=float, default=0.85)
parser.add_argument('--max_tokens', type=int, default=8192)
args = parser.parse_args()

# cuda visible devices
cuda_visible_devices = ','.join(args.d)
os.environ['CUDA_VISIBLE_DEVICES'] = cuda_visible_devices

# load tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    pretrained_model_name_or_path=args.tknz_path,
    trust_remote_code=True,
)

# load vLLM
llm = LLM(
    args.path,
    seed=random.randint(0, 99_999_999),
    dtype='float16',
    max_model_len=args.max_model_len,
    tensor_parallel_size=len(args.d),
    gpu_memory_utilization=args.gpu_memory_utilization,
    trust_remote_code=True,
    skip_tokenizer_init=True,
)

# Flask API
app = Flask(__name__)
CORS(app)


@app.route(f'/completions', methods=['POST'])
def completions():
    content = request.json
    prompt = content['prompt']

    if isinstance(prompt, str):
        prompt = [{'role': 'user', 'content': prompt.strip()}]

    inputs = [tokenizer.apply_chat_template(prompt, add_generation_prompt=True)]
    params: dict = content.get('params')

    temperature = params.get('temperature', 1.0) if params.get('temperature', 1.0) is not None else 1.0
    top_p = params.get('tpo_p', 1.0) if params.get('tpo_p', 1.0) is not None else 1.0

    sampling_params = SamplingParams(temperature=temperature,
                                     top_p=top_p,
                                     max_tokens=args.max_tokens)
    output = llm.generate(prompt_token_ids=inputs,
                          sampling_params=sampling_params,
                          use_tqdm=False)[0]
    output_token_ids = output.outputs[0].token_ids
    response = tokenizer.decode(output_token_ids, skip_special_tokens=True)

    # clear cache
    gc.collect()
    if torch.cuda.device_count() > 0:
        torch.cuda.empty_cache()

    return jsonify({'content': [response]})


if __name__ == '__main__':
    app.run(host=args.host, port=args.port, threaded=False)
