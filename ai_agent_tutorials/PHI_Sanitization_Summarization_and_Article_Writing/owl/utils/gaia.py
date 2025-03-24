# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
import sys

sys.path.append("../")

import json
import random
import re
import string
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union, Tuple

from tqdm import tqdm
from camel.benchmarks import BaseBenchmark
from camel.tasks import Task
from camel.logger import get_logger

from .common import extract_pattern
from .enhanced_role_playing import run_society, OwlGAIARolePlaying

logger = get_logger(__name__)


class GAIABenchmark(BaseBenchmark):
    r"""GAIA Benchmark adapted from `"GAIA: a benchmark for General AI
    Assistants"
    <https://huggingface.co/datasets/gaia-benchmark/GAIA>`_.

    Args:
        data_dir (str): The directory to save the data.
        save_to (str): The file to save the results.
        processes (int, optional): The number of processes to use.
            (default: :obj:`1`)
    """

    def __init__(
        self,
        data_dir: str,
        save_to: str,
        processes: int = 1,
    ):
        r"""Initialize the GAIA benchmark.

        Args:
            data_dir (str): The directory to save the data.
            save_to (str): The file to save the results.
            processes (int, optional): The number of processes to use for
                parallel processing. (default: :obj:`1`)
        """
        super().__init__("gaia", data_dir, save_to, processes)

    def download(self):
        r"""Download the GAIA dataset."""
        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id="gaia-benchmark/GAIA",
            repo_type="dataset",
            local_dir=self.data_dir,
            local_dir_use_symlinks=True,
        )

    def _check_task_completed(self, task_id: str) -> bool:
        for data in self._results:
            if data["task_id"] == task_id:
                return True
        return False

    def dump_tasks(self, save_path: str, datas):
        constructed_data = []
        for idx, data in enumerate(datas):
            tmp_dict = {
                "idx": idx,
                "task_id": data["task_id"],
                "Question": data["Question"],
                "Level": data["Level"],
                "Final answer": data["Final answer"],
                "Annotation Metadata": data["Annotator Metadata"],
            }

            constructed_data.append(tmp_dict)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(constructed_data, f, indent=4)
        f.close()

        print(f"Successfully dumped tasks to {save_path}")

    def load(self, force_download=False):
        r"""Load the GAIA dataset.

        Args:
            force_download (bool, optional): Whether to
                force download the data.
        """
        if force_download:
            logger.info("Force downloading data.")
            self.download()

        # Define validation and test directories
        valid_dir = self.data_dir / "2023/validation"
        test_dir = self.data_dir / "2023/test"

        # Check if directories exist; if not, download the data
        if not valid_dir.is_dir() or not test_dir.is_dir():
            logger.info("Data not found. Downloading data.")
            self.download()

        # Load metadata for both validation and test datasets
        for path, label in zip([valid_dir, test_dir], ["valid", "test"]):
            self._data[label] = []
            with open(path / "metadata.jsonl", "r") as f:
                lines = f.readlines()
                for line in lines:
                    data = json.loads(line)
                    if data["task_id"] == "0-0-0-0-0":
                        continue
                    if data["file_name"]:
                        data["file_name"] = path / data["file_name"]
                    self._data[label].append(data)
        return self

    @property
    def train(self):
        r"""Get the training set."""
        raise NotImplementedError("GAIA does not have a training set.")

    def run(
        self,
        user_role_name: str,
        assistant_role_name: str,
        user_agent_kwargs: dict,
        assistant_agent_kwargs: dict,
        on: Literal["train", "valid", "test"],
        level: Union[int, List[int], Literal["all"]],
        randomize: bool = False,
        subset: Optional[int] = None,
        idx: Optional[List[int]] = None,
        save_result: bool = False,
    ) -> Dict[str, Any]:
        # Validate inputs
        if on not in ["valid", "test"]:
            raise ValueError(
                f"Invalid value for `on`: {on}, expected 'valid' or 'test'."
            )

        levels = (
            [1, 2, 3]
            if level == "all"
            else [level]
            if isinstance(level, int)
            else level
        )
        if not all(isinstance(level, int) and level in [1, 2, 3] for level in levels):
            raise ValueError(
                f"Invalid value for `level`: {level}, expected 1, 2, 3 " "or 'all'."
            )
        logger.info(f"Running benchmark on {on} set at levels {levels}.")
        datas = [data for data in self._data[on] if data["Level"] in levels]
        # Shuffle and subset data if necessary
        if randomize:
            random.shuffle(datas)
        if subset:
            datas = datas[:subset]

        if idx is not None:
            # pick only the tasks with the specified idx
            if len(idx) != 0:
                datas = [datas[i] for i in idx]

        logger.info(f"Number of tasks: {len(datas)}")

        self._results = []

        if save_result:
            try:
                with open(self.save_to, "r", encoding="utf-8") as f:
                    self._results = json.load(f)
                f.close()
            except Exception as e:
                logger.warning(e)
                # raise FileNotFoundError(f"{self.save_to} does not exist.")
        datas = [
            data for data in datas if not self._check_task_completed(data["task_id"])
        ]
        logger.info(f"Number of tasks to be processed: {len(datas)}")
        # Process tasks
        for task in tqdm(datas, desc="Running"):
            if_prepared_task, info = self._prepare_task(task)
            if not if_prepared_task:
                _result_info = {
                    "task_id": task["task_id"],
                    "question": task["Question"],
                    "level": task["Level"],
                    "model_answer": None,
                    "ground_truth": None,
                    "score": 0,
                    "history": None,
                }
                self._results.append(_result_info)
                continue
            try:
                logger.info(f"Task Question: {task['Question']}")
                logger.info(f"Required tools: {task['Annotator Metadata']['Tools']}")

                task_kwargs = {
                    "task_prompt": task["Question"],
                    "with_task_specify": False,
                }

                society = OwlGAIARolePlaying(
                    **task_kwargs,
                    user_role_name=user_role_name,
                    user_agent_kwargs=user_agent_kwargs,
                    assistant_role_name=assistant_role_name,
                    assistant_agent_kwargs=assistant_agent_kwargs,
                )

                raw_answer, chat_history, token_info = run_society(society)
                try:
                    answer = extract_pattern(raw_answer, "final_answer")
                except Exception as e:
                    logger.error(
                        f"Error in extracting final answer from text {raw_answer}: {e}"
                    )
                    answer = None

                logger.info(
                    f"Model answer: {answer}, Ground truth: {task['Final answer']}"
                )

                _result_info = {
                    "task_id": task["task_id"],
                    "question": task["Question"]
                    + "Please decompose the task into several sub-tasks and find the answer step-by-step.",
                    "level": task["Level"],
                    "model_answer": answer,
                    "ground_truth": task["Final answer"],
                    "score": self.question_scorer(answer, task["Final answer"]),
                    "token_info": token_info,
                    "history": chat_history,
                }
                self._results.append(_result_info)

            except Exception as e:
                logger.error(f"Error in processing task: {e}")

            if save_result:
                with open(self.save_to, "w") as f:
                    json.dump(self._results, f, indent=4, ensure_ascii=False)
                f.close()

        return self._generate_summary()

    def _prepare_task(self, task: Dict[str, Any]) -> Tuple[bool, str]:
        r"""Prepare the task by validating and enriching its data."""
        if task["file_name"]:
            if isinstance(task["file_name"], Path):
                task["file_name"] = str(task["file_name"])

            file_path = Path(task["file_name"])
            if not file_path.exists():
                logger.info(f"Skipping task because file not found: {file_path}")
                return False, f"Skipping task because file not found: {file_path}"
            if file_path.suffix in [".pdf", ".docx", ".doc", ".txt"]:
                task["Question"] += (
                    f" Here are the necessary document files: {file_path}"
                )

            elif file_path.suffix in [".jpg", ".jpeg", ".png"]:
                task["Question"] += f" Here are the necessary image files: {file_path}"

            elif file_path.suffix in [".xlsx", "xls", ".csv"]:
                task["Question"] += (
                    f" Here are the necessary table files: {file_path}, for processing excel file, you can write python code and leverage excel toolkit to process the file step-by-step and get the information."
                )

            elif file_path.suffix in [".py"]:
                task["Question"] += f" Here are the necessary python files: {file_path}"

            else:
                task["Question"] += f" Here are the necessary files: {file_path}"

        return True, None

    def _create_task(self, task: Dict[str, Any]) -> Task:
        r"""Create a user message from a task.

        Args:
            task (Dict[str, Any]): The task to create the message from.

        Returns:
            Task: The task created from the input.
        """
        return Task(id=str(task["task_id"]), content=task["Question"])

    def _generate_summary(self) -> Dict[str, Any]:
        r"""Generate and return a summary of the benchmark results."""
        correct = sum(result["score"] for result in self._results)
        return {
            "total": len(self._results),
            "correct": correct,
            "results": self._results,
            "accuracy": correct / len(self._results) if len(self._results) > 0 else 0,
        }

    def question_scorer(self, model_answer: str, ground_truth: str) -> bool:
        r"""Scorer for the GAIA benchmark.
        https://huggingface.co/spaces/gaia-benchmark/leaderboard/blob/main/
        scorer.py

        Args:
            model_answer (str): The model answer.
            ground_truth (str): The ground truth answer.

        Returns:
            bool: The score of the model
        """

        def is_float(element: Any) -> bool:
            try:
                float(element)
                return True
            except ValueError:
                return False

        if is_float(ground_truth):
            logger.info(f"Evaluating {model_answer} as a number.")
            normalized_answer = self.normalize_number_str(model_answer)
            return normalized_answer == float(ground_truth)

        elif any(char in ground_truth for char in [",", ";"]):
            logger.info(f"Evaluating {model_answer} as a comma separated list.")
            gt_elems = self.split_string(ground_truth)
            ma_elems = self.split_string(model_answer)

            if len(gt_elems) != len(ma_elems):
                logger.warning(
                    "Answer lists have different lengths, returning False.",
                    UserWarning,
                )
                return False

            comparisons = []
            for ma_elem, gt_elem in zip(ma_elems, gt_elems):
                if is_float(gt_elem):
                    normalized_ma_elem = self.normalize_number_str(ma_elem)
                    comparisons.append(normalized_ma_elem == float(gt_elem))
                else:
                    ma_elem = self.normalize_str(ma_elem, remove_punct=False)
                    gt_elem = self.normalize_str(gt_elem, remove_punct=False)
                    comparisons.append(ma_elem == gt_elem)
            return all(comparisons)
        else:
            logger.info(f"Evaluating {model_answer} as a string.")
            ma_elem = self.normalize_str(model_answer)
            gt_elem = self.normalize_str(ground_truth)
            return ma_elem == gt_elem

    def normalize_number_str(self, number_str: str) -> float:
        for char in ["$", "%", ","]:
            number_str = number_str.replace(char, "")
        try:
            return float(number_str)
        except ValueError:
            logger.error(f"String {number_str} cannot be normalized to number str.")
            return float("inf")

    def split_string(self, s: str, char_list: Optional[List[str]] = None) -> list[str]:
        r"""Split a string based on a list of characters.

        Args:
            s (str): The string to split.
            char_list (Optional[List[str]], optional): T
                he list of characters to split on.
                (default: :obj:`None`)
        """
        if char_list is None:
            char_list = [",", ";"]
        pattern = f"[{''.join(char_list)}]"
        return re.split(pattern, s)

    def normalize_str(self, input_str, remove_punct=True) -> str:
        r"""Normalize a string.

        Args:
            input_str: The input string to normalize.
            remove_punct: Whether to remove punctuation.

        Returns:
            str: The normalized string.
        """
        no_spaces = re.sub(r"\s", "", input_str)
        if remove_punct:
            translator = str.maketrans("", "", string.punctuation)
            return no_spaces.lower().translate(translator)
        else:
            return no_spaces.lower()
