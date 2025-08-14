from __future__ import annotations

import copy
import json
import os.path
import re

from tqdm.auto import tqdm

from .funsearch import FunSearch
from .profiler import FunSearchProfiler
from .programs_database import ProgramsDatabase
from ...base import TextFunctionProgramConverter as tfpc, Function


def _get_latest_db_json(log_path: str):
    path = os.path.join(log_path, 'prog_db')
    orders = []
    for p in os.listdir(path):
        order = int(p.split('.')[0].split('_')[1])
        orders.append(order)
    max_o = max(orders)
    return os.path.join(path, f'db_{max_o}.json'), max_o


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


def _resume_db(log_path: str, db_config, template, func_to_evol) -> ProgramsDatabase:
    # ======================================================================================================================
    # [
    #     [{'score': -300, 'functions': [xxx, xxx, xxx, ...]}, {'score': -200, 'functions': [xxx, xxx, xxx, ...]}, {...}],
    #     [{...}, {...}],
    # ]
    # ======================================================================================================================
    path, db_max_o = _get_latest_db_json(log_path)
    print(f'RESUME FunSearch: ProgramDB order: {db_max_o}.', flush=True)
    with open(path, 'r') as f:
        data = json.load(f)
    db = ProgramsDatabase(db_config, template, func_to_evol)
    for isld_id, island in enumerate(data):
        for cluster in island:
            score = cluster['score']
            funcs = cluster['functions']
            funcs = [tfpc.text_to_function(f) for f in funcs]
            for f in funcs:
                db.register_function(f, isld_id, score)
    return db


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


def _resume_pf(log_path: str, pf: FunSearchProfiler, template_func: Function):
    _, db_max_order = _get_latest_db_json(log_path)
    funcs, scores, sample_max_order = _get_all_samples_and_scores(log_path)
    print(f'RESUME FunSearch: Sample order: {sample_max_order}.', flush=True)
    pf.__class__._prog_db_order = db_max_order
    # pf.__class__._num_samples = sample_max_order
    for i in tqdm(range(len(funcs)), desc='Resume FunSearch Profiler'):  # noqa
        f, s = funcs[i], scores[i]  # noqa
        f = _resume_text2func(f, s, template_func)
        pf.register_function(f, resume_mode=True)


def resume_funsearch(fs: FunSearch):
    fs._resume_mode = True
    pf = fs._profiler  # noqa
    log_path = pf._log_dir  # noqa
    # resume program database
    template = tfpc.text_to_program(fs._template_program_str)  # noqa
    template_func = fs._function_to_evolve
    config = fs._config.programs_database  # noqa
    func_to_evol = fs._function_to_evolve_name  # noqa
    db = _resume_db(log_path, config, template, func_to_evol)
    fs._database = db
    # resume profiler
    _resume_pf(log_path, pf, template_func)
    # resume funsearch
    _, _, sample_max_order = _get_all_samples_and_scores(log_path)
    fs._tot_sample_nums = sample_max_order
