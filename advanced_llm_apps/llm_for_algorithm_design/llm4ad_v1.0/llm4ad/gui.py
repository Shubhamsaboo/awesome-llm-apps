# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
# Last Revision: 2025/2/16
#
# ------------------------------- Copyright --------------------------------
# Copyright (c) 2025 Optima Group.
# 
# Permission is granted to use the LLM4AD platform for research purposes. 
# All publications, software, or other works that utilize this platform 
# or any part of its codebase must acknowledge the use of "LLM4AD" and 
# cite the following reference:
# 
# Fei Liu, Rui Zhang, Zhuoliang Xie, Rui Sun, Kai Li, Xi Lin, Zhenkun Wang, 
# Zhichao Lu, and Qingfu Zhang, "LLM4AD: A Platform for Algorithm Design 
# with Large Language Model," arXiv preprint arXiv:2412.17287 (2024).
# 
# For inquiries regarding commercial use or licensing, please contact 
# http://www.llm4ad.com/contact.html
# --------------------------------------------------------------------------

import os
import sys
from datetime import datetime

sys.path.append('../')  # This is for finding all the modules

import pytz
import inspect
import llm4ad

from llm4ad.task import import_all_evaluation_classes
from llm4ad.method import import_all_method_classes_from_subfolders
from llm4ad.tools.llm import import_all_llm_classes_from_subfolders
from llm4ad.tools.profiler.profile import ProfilerBase
# from llm4ad.tools.profiler import import_all_profiler_classes_from_subfolders

import_all_evaluation_classes(os.path.join(os.getcwd(), '../llm4ad/task'))
import_all_method_classes_from_subfolders(os.path.join(os.getcwd(), '../llm4ad/method'))
import_all_llm_classes_from_subfolders(os.path.join(os.getcwd(), '../llm4ad/tools/llm'))
# import_all_profiler_classes_from_subfolders(os.path.join(os.getcwd(), '../llm4ad/tools/profiler'))

# Dynamically import all usable classes from the 'llm4ad' package
for module in [llm4ad.tools.llm, llm4ad.tools.profiler, llm4ad.task, llm4ad.method]:
    globals().update({name: obj for name, obj in vars(module).items() if inspect.isclass(obj)})


def main_gui(llm: dict,
             method: dict,
             evaluation: dict,
             profiler: dict):
    """Executes the optimization process using dynamically loaded components based on provided GUI-configured settings.
    Args:
        llm (dict): A dictionary containing the configuration for the large language model (LLM), including:
            - 'name': The name of the LLM class.
            - Additional parameters required for LLM initialization, such as 'host', 'key', 'model', etc.
        method (dict): A dictionary containing the configuration for the optimization method, including:
            - 'name': The name of the optimization method class.
            - Additional method parameters like 'max_sample_nums', 'max_generations', 'pop_size', etc.
        evaluation (dict): A dictionary containing the configuration for the evaluation method, including:
            - 'name': The name of the evaluation class.
            - Additional evaluation parameters.
        profiler (dict): A dictionary containing the configuration for the profiler, including:
            - 'name': The name of the profiler class.
            - Additional profiler parameters like 'evaluation_name', 'method_name', etc.

    The function dynamically loads the LLM, method, evaluation, and profiler classes using their names specified in the dictionaries.
    It then initializes each component with its respective parameters and runs the optimization process.
    The function filters the parameter dictionaries to pass the appropriate arguments to each class initializer.

    Example:
        llm_config = {
            'name': 'HttpsApi',
            'host': 'api.example.com',
            'key': 'your-api-key',
            'model': 'gpt-4-mini'
        }
        method_config = {
            'name': 'EoH',
            'max_sample_nums': 100,
            'max_generations': 10,
            'pop_size': 20,
            'num_samplers': 4,
            'num_evaluators': 4
        }
        evaluation_config = {
            'name': 'OBPEvaluation'
        }
        profiler_config = {
            'name': 'EoHTensorboardProfiler'
        }

        main_gui(llm_config, method_config, evaluation_config, profiler_config)
        """

    profiler_case = globals()[profiler['name']]
    llm_case = globals()[llm['name']]
    method_case = globals()[method['name']]
    eval_case = globals()[evaluation['name']]

    profiler = profiler_case(evaluation_name=evaluation['name'],
                             method_name=method['name'],
                             log_dir=profiler['log_dir'], log_style='complex',create_random_path=False, final_log_dir=profiler['log_dir'])

    llm.pop('name')

    # Filter dict to pass only recognized arguments
    method_params = {key: value for key, value in method.items()}
    llm_params = {key: value for key, value in llm.items()}
    evaluation_params = {key: value for key, value in evaluation.items()}

    llm_case = llm_case(**llm_params)
    eval_case = eval_case(**evaluation_params)
    method_case = method_case(llm=llm_case,
                              profiler=profiler,
                              evaluation=eval_case,
                              **method_params)
    method_case.run()


if __name__ == '__main__':
    llm = {
        'name': 'HttpsApi',
        'host': "api.bltcy.top",
        'key': "",
        'model': "gpt-4o-mini"
    }

    method = {
        'name': 'EoH',
        'max_sample_nums': 200,
        'max_generations': 10,
        'pop_size': 10,
        'num_samplers': 4,
        'num_evaluators': 4
    }

    evaluation = {
        'name': 'OBPEvaluation',
        'data_file': 'weibull_train.pkl',
        'data_key': 'weibull_5k_train'
    }

    temp_str1 = evaluation['name']
    temp_str2 = method['name']
    process_start_time = datetime.now(pytz.timezone("Asia/Shanghai"))
    b = os.path.abspath('..')
    log_folder = b + '/llm4ad/logs/' + process_start_time.strftime(
        "%Y%m%d_%H%M%S") + f'_{temp_str1}' + f'_{temp_str2}'

    profiler = {
        'name': 'ProfilerBase',
        'log_dir': log_folder
    }

    # Example
    main_gui(llm=llm,
             method=method,
             evaluation=evaluation,
             profiler=profiler)  # Enter parameters here
