
template_program = '''
import math
import numpy as np

def priority(el: tuple[int, ...], n: int = 15, w: int = 10) -> float:
    """Returns the priority with which we want to add `el` to the set.
    Args:
        el: the unique vector has the same number w of non-zero elements.
        n : length of the vector.
        w : number of non-zero elements.
    """
    return 0.
'''

task_description = """\
Help me design a novel algorithm to evaluate vectors for potential inclusion in a set. 
This involves iteratively scoring the priority of adding a vector 'el' to the set based on analysis (like bitwise), 
with the objective of maximizing the set's size.
"""

