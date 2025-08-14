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
from llm4ad.task.optimization.co_bench.euclidean_steiner_problem_co_bench.template import template_program, task_description

__all__ = ['ESPEvaluationCB']


class ESPEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Euclidean Steiner problem")
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
                    result = eva(j['points'])
                    fitness = self.eval_func(points=j['points'], steiner_points=result['steiner_points'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)  # itself is a maximum problem

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads the input string and returns a list of individual test problems.
        The input file may contain one or more cases. Each case is expected to follow the format:
           Line 1: An integer m representing the number of test problems in the case.
           For each test problem:
               Line 1: An integer n representing the number of points.
               Next n lines: Two space-separated floating-point numbers for the x- and y-coordinates.
        Returns:
           A list of dictionaries. Each dictionary corresponds to one test problem and contains:
             - "points": a list of (x, y) tuples representing the terminals.
        The function ignores empty lines and supports multiple cases concatenated in one file.
        """
        all_lines = [line.strip() for line in input_string.split('\n')]

        problems = []
        idx = 0
        while idx < len(all_lines):
            # Read number of test problems for this case.
            try:
                m = int(all_lines[idx])
            except Exception as e:
                raise ValueError(f"Expected an integer for number of test problems at line {idx + 1}: {e}")
            idx += 1
            for i in range(m):
                if idx >= len(all_lines):
                    raise ValueError(f"Insufficient data for test problem {i + 1} in a case.")
                try:
                    n = int(all_lines[idx])
                except Exception as e:
                    raise ValueError(f"Expected an integer for number of points at line {idx + 1}: {e}")
                idx += 1
                pts = []
                for j in range(n):
                    if idx >= len(all_lines):
                        raise ValueError(f"Insufficient point data for test problem {i + 1}, point {j + 1}.")
                    parts = all_lines[idx].split()
                    if len(parts) < 2:
                        raise ValueError(f"Test problem {i + 1}: point {j + 1} does not have two coordinates.")
                    try:
                        x, y = float(parts[0]), float(parts[1])
                    except Exception as e:
                        raise ValueError(f"Test problem {i + 1}: invalid coordinate format at point {j + 1}: {e}")
                    pts.append((x, y))
                    idx += 1
                problems.append({"points": pts})
        return problems

    def eval_func(self, **kwargs):
        """
        Evaluates candidate solutions for the Euclidean Steiner Problem.
        Expected kwargs:
          - problems: a list of test problems; each test problem is a dict with key "points"
                      which holds a list of (x, y) tuples representing the original terminals.
          - solutions: a list of candidate solutions, one for each test problem.
                       Each candidate solution is a dict with:
                           - "steiner_points": a list of (x, y) tuples representing the additional Steiner points.
        Evaluation:
          For each test problem:
             1. Compute MST_original, the total length of the Minimum Spanning Tree (MST) computed
                on the original terminals.
             2. Compute candidate_value, the total length of the MST computed on the union of
                the original terminals and the candidate Steiner points.
                (Both MST computations use Euclidean distance where the distance between (x1,y1) and (x2,y2)
                is sqrt((x1-x2)^2 + (y1-y2)^2).)
             3. A valid candidate must have candidate_value ≤ MST_original (within a small tolerance).
                If not, a ValueError is raised.
                Otherwise, the quality ratio is computed as candidate_value / MST_original.
                (A lower ratio indicates a better solution.)
          The overall score is the average of the ratios over all test problems.
        Returns:
          overall_score (float): The average ratio over all test problems.
        """
        import math

        TOL = 1e-6

        def euclidean_distance(a, b):
            return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

        def compute_mst_length(points):
            n = len(points)
            if n == 0:
                return 0.0
            in_mst = [False] * n
            min_dist = [float('inf')] * n
            min_dist[0] = 0.0
            total = 0.0
            for _ in range(n):
                u = -1
                best = float('inf')
                for j in range(n):
                    if not in_mst[j] and min_dist[j] < best:
                        best = min_dist[j]
                        u = j
                if u == -1:
                    break
                in_mst[u] = True
                total += best
                for v in range(n):
                    if not in_mst[v]:
                        d = euclidean_distance(points[u], points[v])
                        if d < min_dist[v]:
                            min_dist[v] = d
            return total

        original_points = kwargs.get("points")
        steiner_points = kwargs.get("steiner_points", [])

        # Compute the MST length on the original terminals.
        mst_original = compute_mst_length(original_points)
        # Compute the candidate tree length as the MST on original terminals plus the candidate Steiner points.
        union_points = original_points + steiner_points
        candidate_value = compute_mst_length(union_points)

        # The candidate MST must not be longer than the MST of the original terminals.
        if candidate_value > mst_original + TOL:
            raise ValueError(
                f"Candidate solution for problem violates constraint: candidate_value ({candidate_value}) > mst_original ({mst_original}).")

        ratio = candidate_value / mst_original if mst_original > 0 else 1.0
        score = 1.0 - ratio
        return score

    def norm_score(self, results):
        optimal_scores = {
            'estein250.txt': [0.03] * 15,
            'estein500.txt': [0.03] * 15,
            'estein1000.txt': [0.03] * 15,
            'estein10000.txt': [0.03],
            'estein100.txt': [0.032423065085033675, 0.03483759951901777, 0.034182167020644916, 0.03248098628546203,
                              0.03310927379936712, 0.034041259411550784, 0.0397677887027611, 0.035660501862228244,
                              0.03502528832071461, 0.03371716889176812, 0.028161233483136594, 0.02687851300146371,
                              0.026629423968470123, 0.03565961816027485, 0.027792022641784153],
            'estein10.txt': [0.04299943461594302, 0.004769960182740007, 0.043782084069761584, 0.011502149990875177,
                             0.024602813181648697, 0.046077835193320094, 0.04426130719672583, 0.015859056215462353,
                             0.02494689613151435, 0.01979275009710557, 0.054874017619661486, 0.005785367498201133,
                             0.06167524682759662, 0.05601469362679634, 0.030685355394374447],
            'estein1.txt': [0.03715248999695819, 2.53248940706996e-08, 0.0, 0.0, 9.429250334525019e-05,
                            0.023970330309954435, 0.01908676366919071, 2.3915825470233187e-05, 0.13381432532245285,
                            0.0295462267220441, 0.056958559892640315, 0.01345616626071433, 0.02629868523014056,
                            0.06795895781452022, 0.0017250989103574366, 0.0, 0.0, 0.06725973598503387,
                            0.037596415595463006, 0.1338944832237634, 0.026412933267079164, 0.018262573283449823,
                            0.02298024555878808, 0.008339962103159793, 0.010573340933293873, 0.001728616561433527,
                            0.0028756538345464655, 0.0, 0.013994227369019674, 0.10179537695309238, 0.07520718237458235,
                            0.05864794152816455, 0.028893309353272167, 0.012207382373579323, 0.006618274407397151,
                            0.023430599555555487, 0.0051899185134780534, 0.007102662306716856, 0.0, 0.04660324576963126,
                            0.007969992389563973, 0.014169307452227442, 0.029004689079907386, 0.00890432342316072,
                            0.024451928874551054, 0.08931639733333341],
            'estein20.txt': [0.043942725618148826, 0.02299597956072552, 0.03725284493193792, 0.02793871516551827,
                             0.03890768508604925, 0.027692754737118963, 0.020995306344934295, 0.047581240549860127,
                             0.015508884273023105, 0.035719166517610645, 0.030072471281848645, 0.04369773360827678,
                             0.031287634487079496, 0.03339355305720737, 0.01641067343311564],
            'estein30.txt': [0.021869824541884353, 0.027617593078341218, 0.02963480155348497, 0.03714277441461655,
                             0.03618276310308932, 0.03148586454727753, 0.03001110334170809, 0.021792810128040463,
                             0.03951202278065513, 0.03211942119280953, 0.020834943979018195, 0.03215928284393588,
                             0.024799825912022122, 0.04963688935942201, 0.025222898338703503],
            'estein40.txt': [0.02609813221879309, 0.03181546093667176, 0.0257617636108477, 0.024867757483739594,
                             0.03878011159818051, 0.033996855652012936, 0.03010133858855013, 0.03474099376571327,
                             0.04407499975387952, 0.036479709224781276, 0.018556418029103017, 0.027092227325115847,
                             0.032442218263355804, 0.034038355193724, 0.03194768623039035],
            'estein50.txt': [0.026375763293115195, 0.03786259604274811, 0.0368858882909211, 0.02843354067948245,
                             0.031562424825947843, 0.03451603250411406, 0.031052490692446644, 0.026042857120256224,
                             0.030847821995874658, 0.028427456323692923, 0.024745303837364396, 0.028489474734615827,
                             0.03501573784622991, 0.02796869646410083, 0.026754142858155694],
            'estein60.txt': [0.033431902683743187, 0.029312387787789773, 0.03673737294505586, 0.029931036026207947,
                             0.038719592946913406, 0.027985371134918502, 0.034956652180465175, 0.02568855514408741,
                             0.03291599372153209, 0.027053357949617274, 0.030189122888249265, 0.03666235385539496,
                             0.037309702462750116, 0.037371343062245765, 0.03292664563821035],
            'estein70.txt': [0.0281926927308368, 0.03822852322564063, 0.02985749535563431, 0.027371582271915496,
                             0.03165937908883898, 0.0319172977507971, 0.03216563529368788, 0.028798544856373787,
                             0.02368422096077183, 0.03141890259642621, 0.03168584881094072, 0.03728987267456063,
                             0.030740662840068156, 0.028285136466959404, 0.03516404960406827],
            'estein80.txt': [0.028927636103650123, 0.027621437956897088, 0.030045750960559836, 0.02154696015188895,
                             0.02208065777296797, 0.028561814513135886, 0.04406481956617947, 0.03559605525407783,
                             0.0387928564376363, 0.029134782330045295, 0.029451055665711712, 0.020408525270118272,
                             0.032505342891095745, 0.038584240577326456, 0.02859138721565424],
            'estein90.txt': [0.03726927391600421, 0.03352718377112174, 0.02689284725659824, 0.027968087207550618,
                             0.040547493724352957, 0.02090677298804755, 0.03565573020648938, 0.030772023917592817,
                             0.030029109853112357, 0.031132625096035427, 0.03504603605103018, 0.026598398815443458,
                             0.02814959463666722, 0.03392597014885834, 0.029514790002086455]
        }

        normed = {}
        for case, (scores, error_message) in results.items():
            if case not in optimal_scores:
                continue  # Skip if there's no optimal score defined.
            optimal_list = optimal_scores[case]
            normed_scores = []
            # Compute normalized score for each index.
            for idx, score in enumerate(scores):
                if isinstance(score, (int, float)):
                    if optimal_list[idx] == 0:
                        normed_scores.append(1.0)
                    else:
                        normed_scores.append(score / optimal_list[idx])
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {'estein1.txt': [5, 43, 37, 26, 38, 27, 25, 9, 42, 0, 4, 34, 36, 24, 3, 10, 15, 13, 12, 8, 20, 23, 14],
               'estein10.txt': [6, 3, 12, 2, 8, 9, 5], 'estein100.txt': [2, 11, 0, 7, 13, 6, 4],
               'estein1000.txt': [9, 6, 1, 5, 7, 14, 3], 'estein20.txt': [13, 2, 3, 14, 0, 4, 8],
               'estein250.txt': [1, 14, 6, 10, 2, 11, 4], 'estein30.txt': [3, 12, 9, 11, 4, 2, 14],
               'estein40.txt': [14, 13, 3, 6, 10, 7, 2], 'estein50.txt': [4, 7, 8, 5, 9, 6, 0],
               'estein500.txt': [12, 11, 4, 8, 1, 9, 0], 'estein60.txt': [14, 0, 2, 8, 12, 9, 7],
               'estein70.txt': [12, 10, 0, 14, 1, 11, 2], 'estein80.txt': [9, 12, 1, 3, 2, 13, 6],
               'estein90.txt': [14, 3, 4, 8, 2, 5, 10]}

        return dev



