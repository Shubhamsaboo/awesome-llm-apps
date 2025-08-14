from __future__ import annotations

from typing import Any
import numpy as np
from template import template_program, task_description
import itertools
from llm4ad.base import Evaluation

__all__ = ['CirclePackingEvaluation']


class CirclePackingEvaluation(Evaluation):
    """Evaluator for circle packing problem in a unit square."""

    def __init__(self,
                 timeout_seconds=30,
                 **kwargs):
        """
        Args:
            timeout_seconds: Time limit for evaluation
            n_instance: Number of problem instances to evaluate
            max_circles: Maximum number of circles to pack (n)
        Raises:
            ValueError: If invalid parameters are provided
        """

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.n = 26

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return self.evaluate(callable_func)

    def verify_circles(self, circles: np.ndarray) -> bool:
        """Checks that the circles are disjoint and lie inside a unit square.

        Args:
            circles: A numpy array of shape (num_circles, 3), where each row is
                of the form (x, y, radius), specifying a circle.

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check pairwise disjointness
            for circle1, circle2 in itertools.combinations(circles, 2):
                center_distance = np.sqrt((circle1[0] - circle2[0]) ** 2 + (circle1[1] - circle2[1]) ** 2)
                radii_sum = circle1[2] + circle2[2]
                if center_distance < radii_sum:
                    return False

            # Check all circles lie inside the unit square [0,1]x[0,1]
            for circle in circles:
                if not (0 <= min(circle[0], circle[1]) - circle[2] and
                        max(circle[0], circle[1]) + circle[2] <= 1):
                    return False
            return True
        except Exception:
            return False



    def plot_circles(self,circles: np.ndarray):

        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        """Plots the circles."""
        _, ax = plt.subplots(1, figsize=(7, 7))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')  # Make axes scaled equally.

        # Draw unit square boundary.
        rect = patches.Rectangle((0, 0), 1, 1, linewidth=1, edgecolor='black', facecolor='none')
        ax.add_patch(rect)

        # Draw the circles.
        for circle in circles:
            circ = patches.Circle((circle[0], circle[1]), circle[2], edgecolor='blue', facecolor='skyblue', alpha=0.5)
            ax.add_patch(circ)

        plt.title(
            f'A collection of {len(circles)} disjoint circles packed inside a unit square to maximize the sum of radii')
        plt.show()

    def evaluate(self, eva: callable) -> float:
        """Evaluate the circle packing solution."""
        circles = eva(self.n)

        #self.plot_circles(circles)
        # Convert to numpy array if not already
        circles = np.array(circles, dtype=np.float64)

        # Verify the solution
        if not self.verify_circles(circles) or len(circles) != self.n:
            return -float('inf')

        # Sum of radii is our score
        score = np.sum(circles[:, 2])

        return score






if __name__ == '__main__':

    # import numpy as np
    #
    #
    # def pack_circles(n: int) -> np.ndarray:
    #     """
    #     Pack n circles in a unit square to maximize sum of radii.
    #
    #     Args:
    #         n: Number of circles to pack
    #
    #     Returns:
    #         Numpy array of shape (n, 3) where each row is (x, y, radius)
    #         All values should be between 0 and 1
    #         Circles must not overlap
    #     """
    #
    #     grid_size = int(np.ceil(np.sqrt(n)))
    #     radius = 0.5 / grid_size
    #
    #     circles = []
    #     for i in range(n):
    #         row = i // grid_size
    #         col = i % grid_size
    #         x = (col + 0.5) / grid_size
    #         y = (row + 0.5) / grid_size
    #         circles.append([x, y, radius])
    #
    #     return np.array(circles)
    import numpy as np
    import math


    def pack_circles(n: int) -> np.ndarray:
        """
        Pack n circles in a unit square to maximize sum of radii.

        Args:
            n: Number of circles to pack

        Returns:
            Numpy array of shape (n, 3) where each row is (x, y, radius)
            All values should be between 0 and 1
            Circles must not overlap
        """
        if n == 0:
            return np.zeros((0, 3))

        circles = np.zeros((n, 3))
        circles[0] = [0.5, 0.5, 0.5]  # Place first circle at center with max possible radius

        for i in range(1, n):
            max_r = 0
            best_pos = (0, 0)

            # Grid search for best position
            grid_size = 100
            for x in np.linspace(0, 1, grid_size):
                for y in np.linspace(0, 1, grid_size):
                    # Calculate minimum distance to existing circles and boundaries
                    min_dist = min(
                        min(np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - cr for cx, cy, cr in circles[:i]),
                        x,
                        1 - x,
                        y,
                        1 - y
                    )

                    if min_dist > max_r:
                        max_r = min_dist
                        best_pos = (x, y)

            circles[i] = [best_pos[0], best_pos[1], max_r]

        return circles


    pack = CirclePackingEvaluation()
    pack.evaluate_program('_', pack_circles)

