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

"""
- Please install following Python packages:
    1. ollama
    2. langchain_ollama
    3. langchain
"""
from langchain_ollama import OllamaLLM
from typing import Any
from ...base import LLM


class LocalOllamaLLM(LLM):
    def __init__(self, model_name: str, **ollama_llm_init_params):
        """Deploy Ollama model on local devices.
        Args:
            model_name            : name of local Ollama model checkpoint.
            ollama_llm_init_params: initialization params for `langchain_ollama.OllamaLLM`.
        """
        super().__init__()
        self.model = OllamaLLM(model=model_name, **ollama_llm_init_params)

    def draw_sample(self, prompt: str | Any, *args, **kwargs) -> str:
        response = self.model.invoke(prompt)
        return response


if __name__ == '__main__':
    model = LocalOllamaLLM('qwen3:14b')
    print(model.draw_sample('hello'))