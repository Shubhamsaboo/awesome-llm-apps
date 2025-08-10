from __future__ import annotations

import copy
import json
import os.path
import re

from tqdm.auto import tqdm

from .reevo import ReEvo
from .profiler import ReEvoProfiler
from .population import Population
from ...base import TextFunctionProgramConverter as tfpc, Function


def _get_latest_pop_json(log_path: str):
    path = os.path.join(log_path, 'population')
    orders = []
    for p in os.listdir(path):
        order = int(p.split('.')[0].split('_')[1])
        orders.append(order)
    max_o = max(orders)
    return os.path.join(path, f'pop_{max_o}.json'), max_o


def _get_all_samples_and_scores(path, get_algorithm=True):
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


def _resume_pop(log_path: str, pop_size) -> Population:
    path, max_gen = _get_latest_pop_json(log_path)
    print(f'RESUME ReEvo: Generations: {max_gen}.', flush=True)
    with open(path, 'r') as f:
        data = json.load(f)
    pop = Population(pop_size=pop_size)
    for d in data:
        func = d['function']
        func = tfpc.text_to_function(func)
        score = d['score']
        algorithm = d['algorithm']
        func.score = score
        func.algorithm = algorithm
        pop.register_function(func)
    pop._generation = max_gen
    return pop


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


def _resume_pf(log_path: str, pf: ReEvoProfiler, template_func):
    _, db_max_order = _get_latest_pop_json(log_path)
    funcs, scores, sample_max_order, algorithms = _get_all_samples_and_scores(log_path)
    print(f'RESUME ReEvo: Sample order: {sample_max_order}.', flush=True)
    pf.__class__._prog_db_order = db_max_order
    # pf.__class__._num_samples = sample_max_order
    for i in tqdm(range(len(funcs)), desc='Resume ReEvo Profiler'):  # noqa
        f, s, algo = funcs[i], scores[i], algorithms[i]
        f = _resume_text2func(f, s, template_func)
        f.algorithm = algo
        pf.register_function(f, resume_mode=True)


def resume_reevo(reevo: ReEvo, path):
    reevo._resume_mode = True
    pf = reevo._profiler
    log_path = path
    # resume program database
    pop = _resume_pop(log_path, reevo._pop_size)
    reevo._population = pop
    # resume profiler
    template_func = reevo._function_to_evolve
    _resume_pf(log_path, pf, template_func)
    # resume reevo
    _, _, sample_max_order, _ = _get_all_samples_and_scores(log_path)
    reevo._tot_sample_nums = sample_max_order
