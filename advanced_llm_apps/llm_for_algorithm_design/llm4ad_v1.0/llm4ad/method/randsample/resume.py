from __future__ import annotations

import copy
import json
import os.path
import re

from tqdm.auto import tqdm

from .profiler import RandSampleProfiler
from .randsample import RandSample
from ...base import TextFunctionProgramConverter as tfpc, Function


def _get_all_samples_and_scores(path, get_algorithm=False):
    file_dir = os.path.join(path, 'samples')
    # get all file directories
    all_files = os.listdir(file_dir)
    # filer `samples_*.json` files and ignore `samples_best.json`
    sample_files = [f for f in all_files if f.startswith('samples_') and f != 'samples_best.json']

    def extract_number(filename):
        # match the first number of the filename
        match = re.search(r'samples_(\d+)~', filename)
        if match:
            return int(match.group(1))
        return 0

    sorted_files = sorted(sample_files, key=extract_number)

    all_func = []
    all_score = []
    all_algorithm = []
    max_o = 0  # the max sample orders

    for file in sorted_files:
        file_path = os.path.join(file_dir, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            samples = json.load(f)
            for sample in samples:
                func = sample['function']
                acc = sample['score'] if sample['score'] else float('-inf')
                all_func.append(func)
                all_score.append(acc)
                all_algorithm.append(sample['algorithm'])
                max_o = sample['sample_order']

    if get_algorithm:
        return all_func, all_score, max_o, all_algorithm
    return all_func, all_score, max_o


def _resume_text2func(f, s, template_func: Function):
    temp = copy.deepcopy(template_func)
    f = tfpc.text_to_function(f)
    if f is None:
        temp.body = '    pass'
        temp.score = None
        return temp
    else:
        f.score = s
        return f


def _resume_pf(log_path: str, pf: RandSampleProfiler, template_func: Function):
    funcs, scores, sample_max_order = _get_all_samples_and_scores(log_path)
    print(f'RESUME RandSample: Sample order: {sample_max_order}.', flush=True)
    # pf.__class__._num_samples = sample_max_order
    for i in tqdm(range(len(funcs)), desc='Resume RandSample Profiler'):  # noqa
        f, s = funcs[i], scores[i]  # noqa
        f = _resume_text2func(f, s, template_func)
        pf.register_function(f, resume_mode=True)


def resume_randsample(rs: RandSample):
    rs._resume_mode = True
    pf = rs._profiler
    assert pf is not None
    log_path = pf._log_dir

    # resume profiler
    template_func = rs._function_to_evolve
    _resume_pf(log_path, pf, template_func)

    # resume rand sample
    funcs, scores, sample_max_order = _get_all_samples_and_scores(log_path)
    rs._tot_sample_nums = sample_max_order
