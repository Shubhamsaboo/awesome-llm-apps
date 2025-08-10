import copy
import pickle
import random
import socket
from queue import Queue
from typing import List, Any, Dict
import requests

from ....base import LLM
import subprocess
import sys
import time
import os
from typing import List
import numpy as np
import json


class VLLMManager:
    def __init__(self):
        self.processes = []

    def deploy_models(self,
                      model_path: str,
                      tknz_path: str,
                      gpus: List[int],
                      ports: List[int],
                      gpu_mem_utils: float | List[float] = None):
        if len(gpus) != len(ports):
            raise ValueError('len(gpus) != len(ports)')

        if gpu_mem_utils is None:
            gpu_mem_utils = [0.85] * len(ports)
        elif isinstance(gpu_mem_utils, float):
            gpu_mem_utils = [gpu_mem_utils] * len(ports)

        executable_path = sys.executable
        for gpu, port, mem_util in zip(gpus, ports, gpu_mem_utils):
            cmd = [
                executable_path,
                os.path.join(os.path.dirname(__file__), 'vllm_llama.py'),
                '--d', str(gpu),
                '--path', model_path,
                '--tknz_path', tknz_path,
                '--port', str(port),
                '--gpu_memory_utilization', str(mem_util),
            ]
            # start subprocess
            process = subprocess.Popen(cmd)
            self.processes.append(process)
            print(f'Start LLM service on GPU: {gpu}, port: {port}, PID: {process.pid}.')
            time.sleep(2)
        print('Start all LLM service.')

    def release_resources_(self):
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f'Terminate process: {process.pid}')
            except subprocess.TimeoutExpired:
                process.kill()
                print(f'Kill process: {process.pid}')
        self.processes = []
        print('Release all resources.')

    def release_resources(self):
        # Kill all child processes first
        for process in self.processes:
            try:
                # Get child processes before terminating parent
                try:
                    import psutil
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                except (ImportError, psutil.NoSuchProcess):
                    children = []

                # Terminate parent process
                process.terminate()
                process.wait(timeout=5)
                print(f'Terminated process: {process.pid}')

                # Kill any remaining children
                for child in children:
                    try:
                        child.terminate()
                        child.wait(timeout=2)
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass

            except subprocess.TimeoutExpired:
                process.kill()
                print(f'Killed process: {process.pid}')

        self.processes = []

        # Force GPU memory cleanup
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print('Cleared CUDA cache')
        except ImportError:
            pass

        print('Released all resources.')


class LocalVLLMAPI(LLM):
    def __init__(self,
                 model_path,
                 tknz_path,
                 gpus: List[int],
                 ports: List[int],
                 **kwargs):
        """Deploy multiple LLMs on multiple GPUs using VLLM backends.
        Currently only support deploying each LLM on single GPU.

        Args:
            model_path: pretrained model path
            tknz_path : tokenizer path
            gpus      : gpu ids where you want to deploy an LLM.
            ports:    :
        """
        super().__init__()
        self.ports = ports
        self.vllm = VLLMManager()
        self.vllm.deploy_models(model_path, tknz_path, gpus, ports)
        self.available_ports = Queue()

        for port in self.ports:
            self.available_ports.put(port)

    def draw_sample(self, prompt, *args, **kwargs) -> str:
        while True:
            port = self.available_ports.get()
            try:
                url = f'http://127.0.0.1:{port}/completions'
                response = self._do_request(prompt, url)
                return response
            except:
                continue
            finally:
                self.available_ports.put(port)

    def _do_request(self, content: str, url: str) -> str:
        content = content.strip('\n').strip()
        data = {
            'prompt': content,
            'params': {
                'max_new_tokens': 4096
            }
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            response = response.json()['content']
            return response[0]

    def __del__(self):
        self.close()

    def close(self):
        self.vllm.release_resources()



