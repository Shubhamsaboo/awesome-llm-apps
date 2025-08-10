from __future__ import annotations

import copy
import json
import os.path

from tqdm.auto import tqdm

from .moead import MOEAD
from .profiler import MOEADProfiler
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


def _get_all_samples_and_scores(path):
    path = os.path.join(path, 'samples')

    def path_to_int(path):
        num = int(path.split('.')[0].split('_')[1])
        return num

    all_func = []
    all_score = []
    dirs = list(os.listdir(path))
    dirs = sorted(dirs, key=path_to_int)
    max_o = path_to_int(dirs[-1])

    for dir in dirs:
        file_name = os.path.join(path, dir)
        with open(file_name, 'r') as f:
            sample = json.load(f)
        func = sample['function']
        acc = sample['score'] if sample['score'] else float('-inf')
        all_func.append(func)
        all_score.append(acc)

    return all_func, all_score, max_o


def _resume_pop(log_path: str, pop_size) -> Population:
    path, max_gen = _get_latest_pop_json(log_path)
    print(f'RESUME MOEAD: Generations: {max_gen}.', flush=True)
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


def _resume_pf(log_path: str, pf: MOEADProfiler, template_func):
    _, db_max_order = _get_latest_pop_json(log_path)
    funcs, scores, sample_max_order = _get_all_samples_and_scores(log_path)
    print(f'RESUME MOEAD: Sample order: {sample_max_order}.', flush=True)
    pf.__class__._prog_db_order = db_max_order
    # pf.__class__._num_samples = sample_max_order
    for i in tqdm(range(len(funcs)), desc='Resume MOEAD Profiler'):  # noqa
        f, s = funcs[i], scores[i]  # noqa
        f = _resume_text2func(f, s, template_func)
        pf.register_function(f, resume_mode=True)


def resume_moead(moead: MOEAD):
    moead._resume_mode = True
    pf = moead._profiler
    log_path = pf._log_dir
    # resume program database
    pop = _resume_pop(log_path, moead._pop_size)
    moead._population = pop
    # resume profiler
    template_func = moead._function_to_evolve
    _resume_pf(log_path, pf, template_func)
    # resume moead
    _, _, sample_max_order = _get_all_samples_and_scores(log_path)
    moead._tot_sample_nums = sample_max_order
