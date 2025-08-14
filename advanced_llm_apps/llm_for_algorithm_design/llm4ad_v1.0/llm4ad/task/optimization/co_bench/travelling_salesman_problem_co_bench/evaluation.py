# References:
#   - Sun, W., Feng, S., Li, S., & Yang, Y. Co-bench: Benchmarking language
#       model agents in algorithm search for combinatorial optimization.
#       arXiv preprint arXiv:2504.04310 (2025).
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

from __future__ import annotations

from typing import Any
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.co_bench.utils import load_subdir_as_text
from llm4ad.task.optimization.co_bench.travelling_salesman_problem_co_bench.template import template_program, task_description

__all__ = ['TSPEvaluationCB']


class TSPEvaluationCB(Evaluation):

    def __init__(self,
                 timeout_seconds=50,
                 **kwargs):

        """
            Args:
                None
            Raises:
                AttributeError: If the data key does not exist.
                FileNotFoundError: If the specified data file is not found.
        """

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        # Load datasets from Hugging Face
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Travelling salesman problem")
        self._datasets = {}
        for filename in dataset:
            # Join all text rows into a single string
            text_content = '\n'.join([row['text'] for row in dataset[filename]])
            self._datasets[filename] = text_content

    def evaluate_program(self, program_str: str, callable_func: callable, **kwargs) -> Any | None:
        return self.evaluate(callable_func)

    def evaluate(self, eva: callable) -> float | None:
        ins_cases = []
        for case_id, ins in enumerate(self._datasets.values()):
            ins_cases.append(self.load_data(ins))

        fitness_list = []
        try:
            for i in ins_cases:
                for j in i:
                    result = eva(j['nodes'])
                    fitness = self.eval_func(j['nodes'], j['tour'], result['tour'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load TSP instances from a file.
        Args:
            file_path (str): Path to the file containing TSP instances
        Returns:
            list: List of dictionaries, each containing a TSP instance with:
                - 'nodes': List of (x, y) coordinates
                - 'tour': List of node indices representing the optimal tour (if available)
        """
        instances = []
        for line in input_string.split('\n'):
            if line.strip():  # Skip empty lines
                line = line.split(" ")
                try:
                    output_idx = line.index('output')
                    num_nodes = output_idx // 2

                    # Extract node coordinates
                    nodes = [(float(line[i]), float(line[i + 1])) for i in range(0, 2 * num_nodes, 2)]

                    # Extract tour (if available)
                    tour = None
                    if output_idx < len(line) - 1:
                        # Convert tour nodes to 0-indexed and exclude the final node (which is the same as the first)
                        tour = [int(node) - 1 for node in line[output_idx + 1:-1]][:-1]

                    instances.append({
                        'nodes': nodes,
                        'tour': tour  # Changed from 'label_tour' to 'tour' to match eval_func
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error processing line: {e}")
                    continue
        return instances

    def eval_func(self, nodes, label_tour, tour):
        """
        Evaluate a predicted TSP tour against a reference tour.
        Args:
            nodes (list): List of (x, y) coordinates representing cities in the TSP problem
                         Format: [(x1, y1), (x2, y2), ..., (xn, yn)]
            label_tour (list): Reference/optimal tour as list of node indices
                              Format: [0, 3, 1, ...] (may be None if no reference available)
            tour (list): Predicted tour from the solver as list of node indices
                             Format: [0, 3, 1, ...]
        Returns:
            float: Optimality gap percentage ((predicted_cost/optimal_cost - 1) * 100)
                   or just the predicted cost if no label_tour is provided
        """
        # Calculate the predicted tour cost
        import math

        num_nodes = len(nodes)

        if len(tour) != num_nodes:
            raise Exception(f"Invalid tour length: Expected {num_nodes}, got {len(tour)}")
        nodes_set = set(tour)

        if len(nodes_set) != num_nodes:
            raise Exception(f"Invalid tour: Contains {len(nodes_set)} unique nodes, expected {num_nodes}")

        expected_nodes = set(range(num_nodes))
        if nodes_set != expected_nodes:
            raise Exception(f"Invalid tour: Contains out-of-range or missing nodes")

        def calculate_tour_cost(nodes, tour):
            cost = 0
            for i in range(len(tour)):
                from_node = tour[i]
                to_node = tour[(i + 1) % len(tour)]  # Wrap around to the first node

                # Calculate Euclidean distance
                from_x, from_y = nodes[from_node]
                to_x, to_y = nodes[to_node]
                segment_cost = math.sqrt((to_x - from_x) ** 2 + (to_y - from_y) ** 2)

                cost += segment_cost

            return cost

        pred_cost = calculate_tour_cost(nodes, tour)

        return pred_cost

    def norm_score(self, results):
        optimal_scores = {
            'tsp10000_test_concorde.txt': [71.77] * 16,
            'tsp1000_test_concorde.txt': [23.180520881091528, 23.185595820967464, 23.015849671324247,
                                          23.537607117355098,
                                          23.437452128607738, 23.31718378127829, 23.337815853824736, 22.98403971254625,
                                          23.056714372610298, 23.344826856094013, 23.204461510197465,
                                          22.739131293587075,
                                          23.188355412394525, 22.89676721383878, 23.321213972552503, 23.288168535452023,
                                          23.40260594371496, 23.379338976209613, 23.373901670260118, 23.217316627245133,
                                          23.237964507712658, 23.468791280324233, 22.921856962988343, 23.10809259424775,
                                          23.370845238521724, 23.241556219224208, 23.348641855759727, 23.53455701244874,
                                          23.385399569524708, 23.324316152061755, 23.600128423871258, 22.97776918106818,
                                          23.23996887566731, 23.39944035075775, 23.21410580402093, 23.093180229981513,
                                          23.41235476581497, 22.907788976836535, 23.023973448563986, 23.38106742108426,
                                          23.015367118079723, 22.610650093362192, 23.728111421819854, 23.31046641124744,
                                          23.25381246570274, 22.889579599261864, 23.138723098665373, 23.228706227395723,
                                          23.420741250703944, 23.255723604641904, 23.63211466330456, 23.03074201227862,
                                          23.08458884685017, 23.241154659459145, 23.445330799785832, 23.315728497380498,
                                          23.262087203582375, 23.43107533587823, 23.020824065107902, 23.591574572456,
                                          23.01019854749962, 23.006394524552746, 23.117390281951273, 23.06132560795126,
                                          22.899650785646813, 23.17319516968116, 23.229133743009296, 23.187607300641957,
                                          22.83150095703399, 23.158901255572648, 23.298349320155108, 23.364983773246387,
                                          23.265256805650658, 23.73268837357109, 23.07144480109362, 23.202894990560697,
                                          23.34293044019312, 23.027139320724427, 23.005485112127072, 23.16783838686215,
                                          23.505726302417372, 23.002594549857108, 23.50388356372942, 23.147934207287026,
                                          23.149537479144914, 23.20934617772166, 23.591015529376406, 23.04614917635098,
                                          23.253196613627406, 23.608716670166032, 23.313874804840438, 23.14887954791675,
                                          23.261925104915175, 23.283273388936596, 22.869470302805432, 23.28919260955595,
                                          23.291061784892037, 23.26303190269252, 23.43192602385145, 22.992654709729297,
                                          23.53527899384453, 23.040088044723632, 23.165752550718327, 23.346603825959306,
                                          23.21040140495141, 23.346553301777227, 23.192654754892565, 23.30425312678073,
                                          23.03197099577737, 23.33672313379179, 23.209507048094107, 23.33316267340018,
                                          22.832592819311447, 23.47921422142005, 23.29841589882617, 22.79469376239716,
                                          23.437580101042798, 22.90129840984213, 23.377778449705787, 23.152730269355438,
                                          23.179248710299515, 23.150584655373375, 23.303559153530237,
                                          23.567343754278223,
                                          23.14174465613352, 23.236813383632978, 23.178718844944385,
                                          23.114735241004848],
            'tsp500_test_concorde.txt': [16.43849479258626, 16.30760609977988, 16.55368794754589, 17.0916769200107,
                                         16.358815620695264, 16.355575136034258, 16.468449176999673, 16.547487678806803,
                                         16.624118787814286, 16.875851583784797, 16.584382768436186, 16.775629024699168,
                                         16.625112093123217, 16.537041048883633, 16.211908886171635, 16.507889182815646,
                                         16.443711824038594, 16.772997858965947, 16.576148488026003, 16.644182889540385,
                                         16.83104599989968, 16.798687309323867, 16.64786310345603, 16.68678554471238,
                                         16.539765290816586, 16.158516162147357, 16.750957469266986, 16.454327423569975,
                                         16.437695592935125, 16.47266324558099, 16.5807314540603, 16.640030608011333,
                                         16.717644006541413, 16.538629003657803, 16.73424552661684, 16.702691981178777,
                                         16.4488503948912, 16.65158792760706, 16.21441667652796, 16.58894596771913,
                                         16.62425057027662, 16.411010231382186, 16.4198250548815, 16.880314028063836,
                                         16.654445215349824, 16.6703557900618, 16.811423319096434, 16.681548608331166,
                                         16.40538961977731, 16.375709814617032, 16.4755439381876, 16.352299703304702,
                                         16.358345088111275, 16.446260979610017, 16.479360821405024, 16.664705227172075,
                                         16.514514381377964, 16.703418138718607, 16.501081465067912, 16.758043371686597,
                                         16.529838521968927, 16.331302381910483, 16.769035549248624, 16.667247187672565,
                                         16.457565298893492, 16.649335805699657, 16.82614018506712, 16.938244810751787,
                                         16.7896287123959, 16.45162524049444, 16.60657770837926, 16.752028686357416,
                                         16.538134167181376, 16.419856051838476, 17.056640374302344, 16.763628081715684,
                                         16.76853264913112, 16.94949524434479, 16.57562195411809, 16.665389374714852,
                                         16.690740743946513, 16.405456340497622, 16.442597689610583, 16.801813848508267,
                                         16.670030108101063, 16.62938726279957, 16.23649751271661, 16.69571793825944,
                                         16.587558708667046, 16.32450912204972, 16.270614173517753, 16.75899873051874,
                                         16.803321805550524, 16.3602825442514, 16.58252109177151, 16.450516009703893,
                                         16.35900041167487, 16.637551343677693, 16.572893477964705, 16.73275661200808,
                                         16.541081653324518, 16.466516697851265, 17.021310751236744, 16.536183906712942,
                                         16.77678089186245, 16.35713000043851, 16.3183776670553, 16.68224023564231,
                                         16.672341313126555, 16.607714934366197, 16.634734868495503, 16.674511551735357,
                                         16.414641537953482, 16.849240225161548, 16.74452644717401, 16.50467692427514,
                                         16.93072503233582, 16.38341557967758, 16.610910144984917, 16.589115661773096,
                                         16.366818207481515, 16.599226446198887, 16.349609487246365, 16.38083156520364,
                                         16.732343248542644, 16.615639804768033, 16.603236295079725, 16.12821378820771]}
        normed = {}
        for case, (scores, error_message) in results.items():
            if case not in optimal_scores:
                continue  # Skip if there's no optimal score defined.
            optimal_list = optimal_scores[case]
            normed_scores = []
            # Compute normalized score for each index.
            for idx, score in enumerate(scores):
                if isinstance(score, (int, float)):
                    normed_scores.append(optimal_list[idx] / score)
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed







