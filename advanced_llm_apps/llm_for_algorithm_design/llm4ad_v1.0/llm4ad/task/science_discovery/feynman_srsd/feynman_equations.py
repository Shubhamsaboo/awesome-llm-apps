from collections import OrderedDict

import numpy as np
import sympy

from .base import KnownEquation
# from .registry import register_eq_class
from .sampling import DefaultSampling, IntegerSampling, SimpleSampling

FEYNMAN_EQUATION_CLASS_List = []  # OrderedDict()
GRAVITATIONAL_CONSTANT = 6.67430e-11
GRAVITATIONAL_ACCELERATION = 9.80665
SPEED_OF_LIGHT = 2.99792458e8
ELECTRIC_CONSTANT = 8.854e-12
PLANCK_CONSTANT = 6.626e-34
BOLTZMANN_CONSTANT = 1.380649e-23
BOHR_MAGNETON = 9.2740100783e-24
DIRAC_CONSTANT = 1.054571817e-34
ELECTRON_MASS = 9.10938356e-31
FINE_STRUCTURE_CONSTANT = 7.2973525693e-3


def register_feynman_eq_class(cls):
    # register_eq_class(cls)
    FEYNMAN_EQUATION_CLASS_List.append(cls)
    return cls


@register_feynman_eq_class
class FeynmanICh6Eq20(KnownEquation):
    """
    - Equation: I.6.20
    - Raw: exp(-(theta / sigma) ** 2 / 2) / (sqrt(2 * pi) * sigma)
    - Num. Vars: 2
    - Vars:
        - x[0]: theta (float)
        - x[1]: sigma (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-i.6.20'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.exp(-(x[0] / x[1]) ** 2 / 2) / (sympy.sqrt(2 * sympy.pi) * x[1])

    def eq_func(self, x):
        return np.exp(-(x[0] / x[1]) ** 2 / 2) / (np.sqrt(2 * np.pi) * x[1])


@register_feynman_eq_class
class FeynmanICh6Eq20a(KnownEquation):
    """
    - Equation: I.6.20a
    - Raw: exp(-theta ** 2 / 2) / sqrt(2 * pi)
    - Num. Vars: 1
    - Vars:
        - x[0]: theta (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.6.20a'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-1, 1.0e1)]

        super().__init__(num_vars=1, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.exp(-x[0] ** 2 / 2) / sympy.sqrt(2 * sympy.pi)

    def eq_func(self, x):
        return np.exp(-x[0] ** 2 / 2) / np.sqrt(2 * np.pi)


@register_feynman_eq_class
class FeynmanICh6Eq20b(KnownEquation):
    """
    - Equation: I.6.20b
    - Raw: exp(-((theta - theta1) / sigma) ** 2 / 2) / (sqrt(2 * pi) * sigma)
    - Num. Vars: 3
    - Vars:
        - x[0]: theta (float)
        - x[1]: theta1 (float)
        - x[2]: sigma (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-i.6.20b'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.exp(-((x[0] - x[1]) / x[2]) ** 2 / 2) / (sympy.sqrt(2 * sympy.pi) * x[2])

    def eq_func(self, x):
        return np.exp(-((x[0] - x[1]) / x[2]) ** 2 / 2)/(np.sqrt(2 * np.pi) * x[2])


@register_feynman_eq_class
class FeynmanICh8Eq14(KnownEquation):
    """
    - Equation: I.8.14
    - Raw: sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    - Num. Vars: 4
    - Vars:
        - x[0]: x2 (float)
        - x[1]: x1 (float)
        - x[2]: y2 (float)
        - x[3]: y1 (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.8.14'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt((x[0] - x[1]) ** 2 + (x[2] - x[3]) ** 2)

    def eq_func(self, x):
        return np.sqrt((x[0] - x[1]) ** 2 + (x[2] - x[3]) ** 2)


@register_feynman_eq_class
class FeynmanICh9Eq18(KnownEquation):
    """
    - Equation: I.9.18
    - Raw: 6.6743e-11 * m1 * m2 / ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
    - Num. Vars: 9
    - Vars:
        - x[0]: m1 (float, positive)
        - x[1]: m2 (float, positive)
        - x[2]: x2 (float)
        - x[3]: x1 (float)
        - x[4]: y2 (float)
        - x[5]: y1 (float)
        - x[6]: z2 (float)
        - x[7]: z1 (float)
    - Constraints:
        - (x[2] - x[3]) ** 2 + (x[4] - x[5]) ** 2 + (x[6] - x[7]) ** 2 != 0
    """
    _eq_name = 'feynman-i.9.18'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            # Consider Cavendish experiment
            sampling_objs = [
                DefaultSampling(1.0, 1.0e3, uses_negative=False),
                DefaultSampling(1.0, 1.0e3, uses_negative=False),
                DefaultSampling(1.0, 1.0e1), DefaultSampling(1.0, 1.0e1), DefaultSampling(1.0, 1.0e1),
                DefaultSampling(1.0, 1.0e1), DefaultSampling(1.0, 1.0e1), DefaultSampling(1.0, 1.0e1)
            ]

        super().__init__(num_vars=8, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = \
            GRAVITATIONAL_CONSTANT * x[0] * x[1] / ((x[2] - x[3]) ** 2 + (x[4] - x[5]) ** 2 + (x[6] - x[7]) ** 2)

    def eq_func(self, x):
        return GRAVITATIONAL_CONSTANT * x[0] * x[1] / ((x[2] - x[3]) ** 2 + (x[4] - x[5]) ** 2 + (x[6] - x[7]) ** 2)


@register_feynman_eq_class
class FeynmanICh10Eq7(KnownEquation):
    """
    - Equation: I.10.7
    - Raw: m_0 / sqrt(1 - v ** 2 / 2.99792458e8 ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: m_0 (float, positive)
        - x[1]: v (float, positive)
    - Constraints:
        - 1 - x[1] ** 2 / 2.99792458e8 ** 2 > 0
    """
    _eq_name = 'feynman-i.10.7'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            # Consider Michelson-Morley experiment
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e5, 1.0e8, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / sympy.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return x[0] / np.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanICh11Eq19(KnownEquation):
    """
    - Equation: I.11.19
    - Raw: x1 * y1 + x2 * y2 + x3 * y3
    - Num. Vars: 6
    - Vars:
        - x[0]: x1 (float)
        - x[1]: y1 (float)
        - x[2]: x2 (float)
        - x[3]: y2 (float)
        - x[4]: x3 (float)
        - x[5]: y3 (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.11.19'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1)
            ]

        super().__init__(num_vars=6, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] + x[2] * x[3] + x[4] * x[5]

    def eq_func(self, x):
        return x[0] * x[1] + x[2] * x[3] + x[4] * x[5]


@register_feynman_eq_class
class FeynmanICh12Eq1(KnownEquation):
    """
    - Equation: I.12.1
    - Raw: mu * Nn
    - Num. Vars: 2
    - Vars:
        - x[0]: mu (float, positive)
        - x[1]: Nn (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-i.12.1'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-2, 1.0, uses_negative=False),
                DefaultSampling(1.0e-2, 1.0, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1]

    def eq_func(self, x):
        return x[0] * x[1]


@register_feynman_eq_class
class FeynmanICh12Eq2(KnownEquation):
    """
    - Equation: I.12.2
    - Raw: q1 * q2 * r / (4 * pi * 8.854e-12 * r ** 3)
    - Num. Vars: 3
    - Vars:
        - x[0]: q1 (float)
        - x[1]: q2 (float)
        - x[2]: r (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-i.12.2'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * x[2] / (4 * sympy.pi * ELECTRIC_CONSTANT * x[2] ** 3)

    def eq_func(self, x):
        return x[0] * x[1] * x[2] / (4 * np.pi * ELECTRIC_CONSTANT * x[2] ** 3)


@register_feynman_eq_class
class FeynmanICh12Eq4(KnownEquation):
    """
    - Equation: I.12.4
    - Raw: q1 * r / (4 * pi * 8.854e-12 * r ** 3)
    - Num. Vars: 2
    - Vars:
        - x[0]: q1 (float)
        - x[1]: r (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-i.12.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / (4 * sympy.pi * ELECTRIC_CONSTANT * x[1] ** 3)

    def eq_func(self, x):
        return x[0] * x[1] / (4 * np.pi * ELECTRIC_CONSTANT * x[1] ** 3)


@register_feynman_eq_class
class FeynmanICh12Eq5(KnownEquation):
    """
    - Equation: I.12.5
    - Raw: q2 * Ef
    - Num. Vars: 2
    - Vars:
        - x[0]: q2 (float)
        - x[1]: Ef (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.12.5'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1]

    def eq_func(self, x):
        return x[0] * x[1]


@register_feynman_eq_class
class FeynmanICh12Eq11(KnownEquation):
    """
    - Equation: I.12.11
    - Raw: q * (Ef + B * v * sin(theta))
    - Num. Vars: 5
    - Vars:
        - x[0]: q (float)
        - x[1]: Ef (float)
        - x[2]: B (float, positive)
        - x[3]: v (float, positive)
        - x[4]: theta (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.12.11'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                SimpleSampling(0.0, np.pi / 2, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (x[1] + x[2] * x[3] * sympy.sin(x[4]))

    def eq_func(self, x):
        return x[0] * (x[1] + x[2] * x[3] * np.sin(x[4]))


@register_feynman_eq_class
class FeynmanICh13Eq4(KnownEquation):
    """
    - Equation: I.13.4
    - Raw: 1 / 2 * m * (v ** 2 + u ** 2 + w ** 2)
    - Num. Vars: 4
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: v (float,)
        - x[2]: u (float)
        - x[3]: w (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.13.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / 2 * x[0] * (x[1] ** 2 + x[2] ** 2 + x[3] ** 2)

    def eq_func(self, x):
        return 1 / 2 * x[0] * (x[1] ** 2 + x[2] ** 2 + x[3] ** 2)


@register_feynman_eq_class
class FeynmanICh13Eq12(KnownEquation):
    """
    - Equation: I.13.12
    - Raw: 6.67430e-11 * m1 * m2 * (1 / r2 - 1 / r1)
    - Num. Vars: 4
    - Vars:
        - x[0]: m1 (float, positive)
        - x[1]: m2 (float, positive)
        - x[2]: r2 (float, positive)
        - x[3]: r1 (float, positive)
    - Constraints:
        - x[2] != 0
        - x[3] != 0
    """
    _eq_name = 'feynman-i.13.12'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-2, 1.0, uses_negative=False), DefaultSampling(1.0e-2, 1.0, uses_negative=False),
                DefaultSampling(1.0e-2, 1.0, uses_negative=False), DefaultSampling(1.0e-2, 1.0, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = GRAVITATIONAL_CONSTANT * x[0] * x[1] * (1 / x[2] - 1 / x[3])

    def eq_func(self, x):
        return GRAVITATIONAL_CONSTANT * x[0] * x[1] * (1 / x[2] - 1 / x[3])


@register_feynman_eq_class
class FeynmanICh14Eq3(KnownEquation):
    """
    - Equation: I.14.3
    - Raw: 9.8066 * m * z
    - Num. Vars: 2
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: z (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.14.3'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-2, 1.0, uses_negative=False), DefaultSampling(1.0e-2, 1.0)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = GRAVITATIONAL_ACCELERATION * x[0] * x[1]

    def eq_func(self, x):
        return GRAVITATIONAL_ACCELERATION * x[0] * x[1]


@register_feynman_eq_class
class FeynmanICh14Eq4(KnownEquation):
    """
    - Equation: I.14.4
    - Raw: 1 / 2 * k_spring * x ** 2
    - Num. Vars: 2
    - Vars:
        - x[0]: k_spring (float, positive)
        - x[1]: x (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-i.14.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e2, 1.0e4, uses_negative=False), DefaultSampling(1.0e-2, 1.0)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / 2 * x[0] * x[1] ** 2

    def eq_func(self, x):
        return 1 / 2 * x[0] * x[1] ** 2


@register_feynman_eq_class
class FeynmanICh15Eq10(KnownEquation):
    """
    - Equation: I.15.10
    - Raw: m_0 * v / sqrt(1 - v ** 2 / 2.99792458e8 ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: m_0 (float, positive)
        - x[1]: v (float)
    - Constraints:
        - 1 - x[1] ** 2 / 2.99792458e8 ** 2 > 0
    """
    _eq_name = 'feynman-i.15.10'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-2, 1.0, uses_negative=False), DefaultSampling(1.0e5, 1.0e7)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / sympy.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return x[0] * x[1] / np.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanICh15Eq3t(KnownEquation):
    """
    - Equation: I.15.3t
    - Raw: (t - u * x / c ** 2) / sqrt(1 - u ** 2 / 2.99792458e8 ** 2)
    - Num. Vars: 3
    - Vars:
        - x[0]: t (float, positive)
        - x[1]: u (float)
        - x[2]: x (float)
    - Constraints:
        - 1 - x[1] ** 2 / 2.99792458e8 ** 2 >= 0
    """
    _eq_name = 'feynman-i.15.3t'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-6, 1.0e-4, uses_negative=False),
                DefaultSampling(1.0e5, 1.0e7), DefaultSampling(1.0, 1.0e2)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (x[0] - x[1] * x[2] / SPEED_OF_LIGHT ** 2) / sympy.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return (x[0] - x[1] * x[2] / SPEED_OF_LIGHT ** 2) / np.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanICh15Eq3x(KnownEquation):
    """
    - Equation: I.15.3x
    - Raw: (x - u * t) / sqrt(1 - u ** 2 / 2.99792458e8 ** 2)
    - Num. Vars: 3
    - Vars:
        - x[0]: x (float)
        - x[1]: u (float)
        - x[2]: t (float)
    - Constraints:
        - 1 - x[1] ** 2 / 2.99792458e8 ** 2 > 0
    """
    _eq_name = 'feynman-i.15.3x'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0, 1.0e2), DefaultSampling(1.0e6, 1.0e8),
                DefaultSampling(1.0e-6, 1.0e-4, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (x[0] - x[1] * x[2]) / sympy.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return (x[0] - x[1] * x[2]) / np.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanICh16Eq6(KnownEquation):
    """
    - Equation: I.16.6
    - Raw: (u + v) / (1 + u * v / 2.99792458e8 ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: u (float)
        - x[1]: v (float)
    - Constraints:
        - 1 + x[0] * x[1] != 0
    """
    _eq_name = 'feynman-i.16.6'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e6, 1.0e8), DefaultSampling(1.0e6, 1.0e8)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (x[0] + x[1]) / (1 + x[0] * x[1] / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return (x[0] + x[1]) / (1 + x[0] * x[1] / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanICh18Eq4(KnownEquation):
    """
    - Equation: I.18.4
    - Raw: (m1 * r1 + m2 * r2) / (m1 + m2)
    - Num. Vars: 4
    - Vars:
        - x[0]: m1 (float, positive)
        - x[1]: r1 (float)
        - x[2]: m2 (float, positive)
        - x[3]: r2 (float)
    - Constraints:
        - x[0] + x[2] != 0
    """
    _eq_name = 'feynman-i.18.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), DefaultSampling(1.0e-1, 1.0e1)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (x[0] * x[1] + x[2] * x[3]) / (x[0] + x[2])

    def eq_func(self, x):
        return (x[0] * x[1] + x[2] * x[3]) / (x[0] + x[2])


@register_feynman_eq_class
class FeynmanICh18Eq12(KnownEquation):
    """
    - Equation: I.18.12
    - Raw: r * F * sin(theta)
    - Num. Vars: 3
    - Vars:
        - x[0]: r (float, positive)
        - x[1]: F (float)
        - x[2]: theta (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.18.12'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * sympy.sin(x[2])

    def eq_func(self, x):
        return x[0] * x[1] * np.sin(x[2])


@register_feynman_eq_class
class FeynmanICh18Eq16(KnownEquation):
    """
    - Equation: I.18.16
    - Raw: m * r * v * sin(theta)
    - Num. Vars: 4
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: r (float, positive)
        - x[2]: v (float)
        - x[3]: theta (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.18.16'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * x[2] * sympy.sin(x[3])

    def eq_func(self, x):
        return x[0] * x[1] * x[2] * np.sin(x[3])


@register_feynman_eq_class
class FeynmanICh24Eq6(KnownEquation):
    """
    - Equation: I.24.6
    - Raw: 1 / 2 * m * (omega ** 2 + omega_0 ** 2) * 1 / 2 * x ** 2
    - Num. Vars: 4
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: omega (float)
        - x[2]: omega_0 (float)
        - x[3]: x (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.24.6'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-1, 1.0e1)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / 2 * x[0] * (x[1] ** 2 + x[2] ** 2) * 1/2 * x[3] ** 2

    def eq_func(self, x):
        return 1 / 2 * x[0] * (x[1] ** 2 + x[2] ** 2) * 1/2 * x[3] ** 2


@register_feynman_eq_class
class FeynmanICh25Eq13(KnownEquation):
    """
    - Equation: I.25.13
    - Raw: q / C
    - Num. Vars: 2
    - Vars:
        - x[0]: q (float)
        - x[1]: C (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-i.25.13'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-5, 1.0e-3), DefaultSampling(1.0e-5, 1.0e-3, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / x[1]

    def eq_func(self, x):
        return x[0] / x[1]


@register_feynman_eq_class
class FeynmanICh26Eq2(KnownEquation):
    """
    - Equation: I.26.2
    - Raw: sin(theta1) / sin(theta2)
    - Num. Vars: 2
    - Vars:
        - x[0]: theta1 (float, positive)
        - x[1]: theta2 (float, positive)
    - Constraints:
        - x[0] * np.sin(x[1]) >= -np.pi /2
        - x[0] * np.sin(x[1]) <= np.pi/2
    """
    _eq_name = 'feynman-i.26.2'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                SimpleSampling(0, np.pi / 2, uses_negative=False), SimpleSampling(0, np.pi / 2, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sin(x[0]) / sympy.sin(x[1])

    def eq_func(self, x):
        return np.sin(x[0]) / np.sin(x[1])


@register_feynman_eq_class
class FeynmanICh27Eq6(KnownEquation):
    """
    - Equation: I.27.6
    - Raw: 1 / (1 / d1 + n / d2)
    - Num. Vars: 3
    - Vars:
        - x[0]: d1 (float, positive)
        - x[1]: n (float, positive)
        - x[2]: d2 (float, positive)
    - Constraints:
        - x[0] != 0
        - x[2] != 0
    """
    _eq_name = 'feynman-i.27.6'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (1 / x[0] + x[1] / x[2])

    def eq_func(self, x):
        return 1 / (1 / x[0] + x[1] / x[2])


@register_feynman_eq_class
class FeynmanICh29Eq4(KnownEquation):
    """
    - Equation: I.29.4
    - Raw: omega / 2.99792458e8
    - Num. Vars: 1
    - Vars:
        - x[0]: omega (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-i.29.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e9, 1.0e11, uses_negative=False)
            ]

        super().__init__(num_vars=1, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / SPEED_OF_LIGHT

    def eq_func(self, x):
        return x[0] / SPEED_OF_LIGHT


@register_feynman_eq_class
class FeynmanICh29Eq16(KnownEquation):
    """
    - Equation: I.29.16
    - Raw: sqrt(x1 ** 2 + x2 ** 2 + 2 * x1 * x2 * cos(theta1 - theta2))
    - Num. Vars: 4
    - Vars:
        - x[0]: x1 (float, positive)
        - x[1]: x2 (float, positive)
        - x[2]: theta1 (float)
        - x[3]: theta2 (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.29.16'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                SimpleSampling(0, 2 * np.pi, uses_negative=False), SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt(x[0] ** 2 + x[1] ** 2 + 2 * x[0] * x[1] * sympy.cos(x[2] - x[3]))

    def eq_func(self, x):
        return np.sqrt(x[0] ** 2 + x[1] ** 2 + 2 * x[0] * x[1] * np.cos(x[2] - x[3]))


@register_feynman_eq_class
class FeynmanICh30Eq3(KnownEquation):
    """
    - Equation: I.30.3
    - Raw: Int_0 * sin(n * theta / 2) ** 2 / sin(theta / 2) ** 2
    - Num. Vars: 3
    - Vars:
        - x[0]: Int_0 (float, positive)
        - x[1]: n (integer, positive)
        - x[2]: theta (float)
    - Constraints:
        - np.sin(x[2] / 2) != 0
    """
    _eq_name = 'feynman-i.30.3'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False), IntegerSampling(1.0e1, 1.0e3, uses_negative=False),
                SimpleSampling(-2 * np.pi, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * sympy.sin(x[1] * x[2] / 2) ** 2 / sympy.sin(x[2] / 2) ** 2

    def eq_func(self, x):
        return x[0] * np.sin(x[1] * x[2] / 2) ** 2 / np.sin(x[2] / 2) ** 2


@register_feynman_eq_class
class FeynmanICh30Eq5(KnownEquation):
    """
    - Equation: I.30.5
    - Raw: lambda / (n * sin(theta))
    - Num. Vars: 3
    - Vars:
        - x[0]: lambda (float, positive)
        - x[1]: n (integer, positive)
        - x[2]: theta (float, positive)
    - Constraints:
        - x[1] != 0
        - x[2] != 0
        - x[2] != pi
    """
    _eq_name = 'feynman-i.30.5'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-11, 1.0e-9, uses_negative=False), IntegerSampling(1.0, 1.0e2, uses_negative=False),
                SimpleSampling(0, np.pi / 2, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (x[1] * sympy.sin(x[2]))

    def eq_func(self, x):
        return x[0] / (x[1] * np.sin(x[2]))


@register_feynman_eq_class
class FeynmanICh32Eq5(KnownEquation):
    """
    - Equation: I.32.5
    - Raw: q ** 2 * a ** 2 / (6 * pi * 8.854e-12 * 2.99792458e8 ** 3)
    - Num. Vars: 4
    - Vars:
        - x[0]: q (float)
        - x[1]: a (float, positive)
    - Constraints:
        - x[2] != 0
        - x[3] != 0
    """
    _eq_name = 'feynman-i.32.5'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e5, 1.0e7, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] ** 2 * x[1] ** 2 / (6 * sympy.pi * ELECTRIC_CONSTANT * SPEED_OF_LIGHT ** 3)

    def eq_func(self, x):
        return x[0] ** 2 * x[1] ** 2 / (6 * np.pi * ELECTRIC_CONSTANT * SPEED_OF_LIGHT ** 3)


@register_feynman_eq_class
class FeynmanICh32Eq17(KnownEquation):
    """
    - Equation: I.32.17
    - Raw: (1 / 2 * 8.854e-12 * 2.99792458e8 * Ef ** 2) * (8 * pi * r ** 2 / 3) * (omega ** 4 / (omega ** 2 - omega_0 ** 2) ** 2)
    - Num. Vars: 4
    - Vars:
        - x[0]: Ef (float)
        - x[1]: r (float, positive)
        - x[2]: omega (float)
        - x[3]: omega_0 (float)
    - Constraints:
        - x[2] ** 2 - x[3] ** 2 != 0
    """
    _eq_name = 'feynman-i.32.17'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e1, 1.0e3), DefaultSampling(1.0e-2, 1.0, uses_negative=False),
                DefaultSampling(1.0e9, 1.0e11), DefaultSampling(1.0e9, 1.0e11)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (1 / 2 * ELECTRIC_CONSTANT * SPEED_OF_LIGHT * x[0] ** 2) \
                        * (8 * sympy.pi * x[1] ** 2 / 3) * (x[2] ** 4 / (x[2] ** 2 - x[3] ** 2) ** 2)

    def eq_func(self, x):
        return (1 / 2 * ELECTRIC_CONSTANT * SPEED_OF_LIGHT * x[0] ** 2) \
               * (8 * np.pi * x[1] ** 2 / 3) * (x[2] ** 4 / (x[2] ** 2 - x[3] ** 2) ** 2)


@register_feynman_eq_class
class FeynmanICh34Eq10(KnownEquation):
    """
    - Equation: I.34.10
    - Raw: omega_0 / (1 - v / 2.99792458e8)
    - Num. Vars: 2
    - Vars:
        - x[0]: omega_0 (float, positive)
        - x[1]: v (float)
    - Constraints:
        - 2.99792458e8 - x[1] != 0
    """
    _eq_name = 'feynman-i.34.10'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e9, 1.0e11, uses_negative=False), DefaultSampling(1.0e5, 1.0e7)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (1 - x[1] / SPEED_OF_LIGHT)

    def eq_func(self, x):
        return x[0] / (1 - x[1] / SPEED_OF_LIGHT)


@register_feynman_eq_class
class FeynmanICh34Eq8(KnownEquation):
    """
    - Equation: I.34.8
    - Raw: q * v * B / p
    - Num. Vars: 4
    - Vars:
        - x[0]: q (float)
        - x[1]: v (float)
        - x[2]: B (float)
        - x[3]: p (float)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-i.34.8'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e5, 1.0e7),
                DefaultSampling(1.0e1, 1.0e3), DefaultSampling(1.0e9, 1.0e11)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * x[2] / x[3]

    def eq_func(self, x):
        return x[0] * x[1] * x[2] / x[3]


@register_feynman_eq_class
class FeynmanICh34Eq14(KnownEquation):
    """
    - Equation: I.34.14
    - Raw: (1 + v / 2.99792458e8) / sqrt(1 - v ** 2 / 2.99792458e8 ** 2) * omega_0
    - Num. Vars: 2
    - Vars:
        - x[0]: v (float)
        - x[1]: omega_0 (float, positive)
    - Constraints:
        - 2.99792458e8 ** 2 - x[0] ** 2 > 0
        - x[1] != 0
    """
    _eq_name = 'feynman-i.34.14'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e6, 1.0e8), DefaultSampling(1.0e9, 1.0e11, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (1 + x[0] / SPEED_OF_LIGHT) / sympy.sqrt(1 - x[0] ** 2 / SPEED_OF_LIGHT ** 2) * x[1]

    def eq_func(self, x):
        return (1 + x[0] / x[1]) / np.sqrt(1 - x[0] ** 2 / x[1] ** 2) * x[1]


@register_feynman_eq_class
class FeynmanICh34Eq27(KnownEquation):
    """
    - Equation: I.34.27
    - Raw: (6.626e-34 / (2 * pi)) * omega
    - Num. Vars: 1
    - Vars:
        - x[0]: omega (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-i.34.27'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e9, 1.0e11, uses_negative=False)]

        super().__init__(num_vars=1, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (PLANCK_CONSTANT / (2 * sympy.pi)) * x[0]

    def eq_func(self, x):
        return (PLANCK_CONSTANT / (2 * np.pi)) * x[0]


@register_feynman_eq_class
class FeynmanICh37Eq4(KnownEquation):
    """
    - Equation: I.37.4
    - Raw: I1 + I2 + 2 * sqrt(I1 * I2) * cos(delta)
    - Num. Vars: 3
    - Vars:
        - x[0]: I1 (float, positive)
        - x[1]: I2 (float, positive)
        - x[2]: delta (float)
    - Constraints:
        - x[0]*x[1] >= 0
    """
    _eq_name = 'feynman-i.37.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False),
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False), SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] + x[1] + 2 * sympy.sqrt(x[0] * x[1]) * sympy.cos(x[2])

    def eq_func(self, x):
        return x[0] + x[1] + 2 * np.sqrt(x[0] * x[1]) * np.cos(x[2])


@register_feynman_eq_class
class FeynmanICh38Eq12(KnownEquation):
    """
    - Equation: I.38.12
    - Raw: 4 * pi * 8.854e-12 * (6.626e-34 / (2 * pi)) ** 2 / (m * q ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: q (float)
    - Constraints:
        - x[0] != 0
        - x[1] != 0
    """
    _eq_name = 'feynman-i.38.12'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-28, 1.0e-26, uses_negative=False),
                DefaultSampling(1.0e-11, 1.0e-9, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 4 * sympy.pi * ELECTRIC_CONSTANT * (PLANCK_CONSTANT / (2 * sympy.pi)) ** 2 / (x[0] * x[1] ** 2)

    def eq_func(self, x):
        return 4 * np.pi * ELECTRIC_CONSTANT * (PLANCK_CONSTANT / (2 * np.pi)) ** 2 / (x[0] * x[1] ** 2)


@register_feynman_eq_class
class FeynmanICh39Eq10(KnownEquation):
    """
    - Equation: I.39.10
    - Raw: 3 / 2 * pr * V
    - Num. Vars: 2
    - Vars:
        - x[0]: pr (float, positive)
        - x[1]: V (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-i.39.10'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e4, 1.0e6, uses_negative=False), DefaultSampling(1.0e-5, 1.0e-3, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 3 / 2 * x[0] * x[1]

    def eq_func(self, x):
        return 3 / 2 * x[0] * x[1]


@register_feynman_eq_class
class FeynmanICh39Eq11(KnownEquation):
    """
    - Equation: I.39.11
    - Raw: 1 / (gamma - 1) * pr * V
    - Num. Vars: 3
    - Vars:
        - x[0]: gamma (float, positive)
        - x[1]: pr (float, positive)
        - x[2]: V (float, positive)
    - Constraints:
        - x[0] - 1 != 0
    """
    _eq_name = 'feynman-i.39.11'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                SimpleSampling(1, 2, uses_negative=False),
                DefaultSampling(1.0e4, 1.0e6, uses_negative=False), DefaultSampling(1.0e-5, 1.0e-3, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (x[0] - 1) * x[1] * x[2]

    def eq_func(self, x):
        return 1 / (x[0] - 1) * x[1] * x[2]


@register_feynman_eq_class
class FeynmanICh39Eq22(KnownEquation):
    """
    - Equation: I.39.22
    - Raw: n * 1.380649e-23 * T / V
    - Num. Vars: 3
    - Vars:
        - x[0]: n (integer, positive)
        - x[1]: T (float, positive)
        - x[2]: V (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-i.39.22'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False), DefaultSampling(1.0e-5, 1.0e-3, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * BOLTZMANN_CONSTANT * x[1] / x[2]

    def eq_func(self, x):
        return x[0] * BOLTZMANN_CONSTANT * x[1] / x[2]


@register_feynman_eq_class
class FeynmanICh40Eq1(KnownEquation):
    """
    - Equation: I.40.1
    - Raw: n_0 * exp(-m * 9.80665 * x / (1.380649e-23 * T))
    - Num. Vars: 4
    - Vars:
        - x[0]: n_0 (float, positive)
        - x[1]: m (float, positive)
        - x[2]: x (float)
        - x[3]: T (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-i.40.1'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e25, 1.0e27, uses_negative=False),
                DefaultSampling(1.0e-24, 1.0e-22, uses_negative=False),
                DefaultSampling(1.0e-2, 1.0), DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * sympy.exp(-x[1] * GRAVITATIONAL_ACCELERATION * x[2] / (BOLTZMANN_CONSTANT * x[3]))

    def eq_func(self, x):
        return x[0] * np.exp(-x[1] * GRAVITATIONAL_ACCELERATION * x[2] / (BOLTZMANN_CONSTANT * x[3]))


@register_feynman_eq_class
class FeynmanICh41Eq16(KnownEquation):
    """
    - Equation: I.41.16
    - Raw: 6.626e-34 / (2 * pi) * omega ** 3 / (pi ** 2 * 2.99792458e8 ** 2 * (exp((6.626e-34 / (2 * pi)) * omega / (1.380649e-23 * T)) - 1))
    - Num. Vars: 2
    - Vars:
        - x[0]: omega (float, positive)
        - x[1]: T (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-i.41.16'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = PLANCK_CONSTANT / (2 * sympy.pi) * x[0] ** 3 / (sympy.pi ** 2 * SPEED_OF_LIGHT ** 2 * (sympy.exp((PLANCK_CONSTANT / (2 * sympy.pi)) * x[0] / (BOLTZMANN_CONSTANT * x[1])) - 1))

    def eq_func(self, x):
        return PLANCK_CONSTANT / (2 * np.pi) * x[0] ** 3 / (np.pi ** 2 * SPEED_OF_LIGHT ** 2 * (np.exp((PLANCK_CONSTANT / (2 * np.pi)) * x[0] / (BOLTZMANN_CONSTANT * x[1])) - 1))


@register_feynman_eq_class
class FeynmanICh43Eq16(KnownEquation):
    """
    - Equation: I.43.16
    - Raw: mu_drift * q * Volt / d
    - Num. Vars: 4
    - Vars:
        - x[0]: mu_drift (float)
        - x[1]: q (float)
        - x[2]: Volt (float)
        - x[3]: d (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-i.43.16'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-6, 1.0e-4), DefaultSampling(1.0e-11, 1.0e-9),
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * x[2] / x[3]

    def eq_func(self, x):
        return x[0] * x[1] * x[2] / x[3]


@register_feynman_eq_class
class FeynmanICh43Eq31(KnownEquation):
    """
    - Equation: I.43.31
    - Raw: mob * 1.380649e-23 * T
    - Num. Vars: 2
    - Vars:
        - x[0]: mob (float, positive)
        - x[1]: T (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-i.43.31'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e13, 1.0e15, uses_negative=False), DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * BOLTZMANN_CONSTANT * x[1]

    def eq_func(self, x):
        return x[0] * BOLTZMANN_CONSTANT * x[1]


@register_feynman_eq_class
class FeynmanICh43Eq43(KnownEquation):
    """
    - Equation: I.43.43
    - Raw: 1 / (gamma - 1) * 1.380649e-23 * v / A
    - Num. Vars: 3
    - Vars:
        - x[0]: gamma (float, positive)
        - x[1]: v (float, positive)
        - x[2]: A (float, positive)
    - Constraints:
        - x[0] - 1 != 0
        - x[2] != 0
    """
    _eq_name = 'feynman-i.43.43'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                SimpleSampling(1, 2, uses_negative=False),
                DefaultSampling(1.0e2, 1.0e4, uses_negative=False),
                DefaultSampling(1.0e-21, 1.0e-19, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (x[0] - 1) * BOLTZMANN_CONSTANT * x[1] / x[2]

    def eq_func(self, x):
        return 1 / (x[0] - 1) * BOLTZMANN_CONSTANT * x[1] / x[2]


@register_feynman_eq_class
class FeynmanICh44Eq4(KnownEquation):
    """
    - Equation: I.44.4
    - Raw: n * 1.380649e-23 * T * ln(V2 / V1)
    - Num. Vars: 4
    - Vars:
        - x[0]: n (integer -> real due to its order, positive)
        - x[1]: T (float, positive)
        - x[2]: V2 (float, positive)
        - x[3]: V1 (float, positive)
    - Constraints:
        - x[3] != 0
        - x[2] / x[3] > 0
    """
    _eq_name = 'feynman-i.44.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(10e24, 10e26, uses_negative=False), DefaultSampling(1.0e1, 1.0e3, uses_negative=False),
                DefaultSampling(1.0e-5, 1.0e-3, uses_negative=False),
                DefaultSampling(1.0e-5, 1.0e-3, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * BOLTZMANN_CONSTANT * x[1] * sympy.log(x[2] / x[3])

    def eq_func(self, x):
        return x[0] * BOLTZMANN_CONSTANT * x[1] * np.log(x[2] / x[3])


@register_feynman_eq_class
class FeynmanICh47Eq23(KnownEquation):
    """
    - Equation: I.47.23
    - Raw: sqrt(gamma * pr / rho)
    - Num. Vars: 3
    - Vars:
        - x[0]: gamma (float, positive)
        - x[1]: pr (float, positive)
        - x[2]: rho (float, positive)
    - Constraints:
        - x[0] * x[1] / x[2] >= 0
        - x[2] != 0
    """
    _eq_name = 'feynman-i.47.23'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                SimpleSampling(1, 2, uses_negative=False), SimpleSampling(5.0e-6, 1.5e-5, uses_negative=False),
                SimpleSampling(1, 2, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt(x[0] * x[1] / x[2])

    def eq_func(self, x):
        return np.sqrt(x[0] * x[1] / x[2])


@register_feynman_eq_class
class FeynmanICh48Eq2(KnownEquation):
    """
    - Equation: I.48.2
    - Raw: m * 2.99792458e8 ** 2 / sqrt(1 - v ** 2 / 2.99792458e8 ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: v (float, positive)
    - Constraints:
        - 1 - x[1] ** 2 / 2.99792458e8 ** 2 > 0
    """
    _eq_name = 'feynman-i.48.2'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-29, 1.0e-27, uses_negative=False),
                DefaultSampling(1.0e6, 1.0e8, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * SPEED_OF_LIGHT ** 2 / sympy.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return x[0] * SPEED_OF_LIGHT ** 2 / np.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanICh50Eq26(KnownEquation):
    """
    - Equation: I.50.26
    - Raw: x1 * (cos(omega * t) + alpha * cos(omega * t) ** 2)
    - Num. Vars: 4
    - Vars:
        - x[0]: x1 (float, positive)
        - x[1]: omega (float)
        - x[2]: t (float, positive)
        - x[3]: alpha (float)
    - Constraints:
    """
    _eq_name = 'feynman-i.50.26'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), DefaultSampling(1.0e1, 1.0e3),
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False), DefaultSampling(1.0e-3, 1.0e-1)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (sympy.cos(x[1] * x[2]) + x[3] * sympy.cos(x[1] * x[2]) ** 2)

    def eq_func(self, x):
        return x[0] * (np.cos(x[1] * x[2]) + x[3] * np.cos(x[1] * x[2]) ** 2)


@register_feynman_eq_class
class FeynmanIICh2Eq42(KnownEquation):
    """
    - Equation: II.2.42
    - Raw: kappa * (T2 - T1) * A / d
    - Num. Vars: 5
    - Vars:
        - x[0]: kappa (float, positive)
        - x[1]: T2 (float, positive)
        - x[2]: T1 (float, positive)
        - x[3]: A (float, positive)
        - x[4]: d (float, positive)
    - Constraints:
        - x[4] != 0
    """
    _eq_name = 'feynman-ii.2.42'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False), DefaultSampling(1.0e1, 1.0e3, uses_negative=False),
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False),
                DefaultSampling(1.0e-4, 1.0e-2, uses_negative=False), DefaultSampling(1.0e-2, 1.0, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (x[1] - x[2]) * x[3] / x[4]

    def eq_func(self, x):
        return x[0] * (x[1] - x[2]) * x[3] / x[4]


@register_feynman_eq_class
class FeynmanIICh3Eq24(KnownEquation):
    """
    - Equation: II.3.24
    - Raw: Pwr / (4 * pi * r ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: Pwr (float)
        - x[1]: r (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-ii.3.24'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0, 1.0e2), DefaultSampling(1.0e-2, 1.0, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (4 * sympy.pi * x[1] ** 2)

    def eq_func(self, x):
        return x[0] / (4 * np.pi * x[1] ** 2)


@register_feynman_eq_class
class FeynmanIICh4Eq23(KnownEquation):
    """
    - Equation: II.4.23
    - Raw: q / (4 * pi * 8.854e-12 * r)
    - Num. Vars: 2
    - Vars:
        - x[0]: q (float)
        - x[1]: r (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-ii.4.23'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-2, 1.0, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (4 * sympy.pi * ELECTRIC_CONSTANT * x[1])

    def eq_func(self, x):
        return x[0] / (4 * np.pi * ELECTRIC_CONSTANT * x[1])


@register_feynman_eq_class
class FeynmanIICh6Eq11(KnownEquation):
    """
    - Equation: II.6.11
    - Raw: 1 / (4 * pi * 8.854e-12) * p_d * cos(theta) / r ** 2
    - Num. Vars: 3
    - Vars:
        - x[0]: p_d (float)
        - x[1]: theta (float)
        - x[2]: r (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-ii.6.11'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-22, 1.0e-20), SimpleSampling(0, 2 * np.pi, uses_negative=False),
                DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (4 * sympy.pi * ELECTRIC_CONSTANT) * x[0] * sympy.cos(x[1]) / x[2] ** 2

    def eq_func(self, x):
        return 1 / (4 * np.pi * ELECTRIC_CONSTANT) * x[0] * np.cos(x[1]) / x[2] ** 2


@register_feynman_eq_class
class FeynmanIICh6Eq15a(KnownEquation):
    """
    - Equation: II.6.15a
    - Raw: p_d / (4 * pi * 8.854e-12) * 3 * z / r ** 5 * sqrt(x ** 2 + y ** 2)
    - Num. Vars: 5
    - Vars:
        - x[0]: p_d (float)
        - x[1]: z (float, positive)
        - x[2]: r (float, positive)
        - x[3]: x (float, positive)
        - x[4]: y (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-ii.6.15a'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-22, 1.0e-20), DefaultSampling(1.0e-10, 1.0e-8),
                DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False), DefaultSampling(1.0e-10, 1.0e-8),
                DefaultSampling(1.0e-10, 1.0e-8)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (4 * sympy.pi * ELECTRIC_CONSTANT) \
                        * 3 * x[1] / x[2] ** 5 * sympy.sqrt(x[3] ** 2 + x[4] ** 2)

    def eq_func(self, x):
        return x[0] / (4 * np.pi * ELECTRIC_CONSTANT) * 3 * x[1] / x[2] ** 5 * np.sqrt(x[3] ** 2 + x[4] ** 2)


@register_feynman_eq_class
class FeynmanIICh6Eq15b(KnownEquation):
    """
    - Equation: II.6.15b
    - Raw: p_d / (4 * pi * 8.854e-12) * 3 * cos(theta) * sin(theta) / r ** 3
    - Num. Vars: 3
    - Vars:
        - x[0]: p_d (float)
        - x[1]: theta (float)
        - x[2]: r (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-ii.6.15b'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-22, 1.0e-20), SimpleSampling(0, np.pi, uses_negative=False),
                DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (4 * sympy.pi * ELECTRIC_CONSTANT) * 3 * sympy.cos(x[1]) * sympy.sin(x[1]) / x[2] ** 3

    def eq_func(self, x):
        return x[0] / (4 * np.pi * ELECTRIC_CONSTANT) * 3 * np.cos(x[1]) * np.sin(x[1]) / x[2] ** 3


@register_feynman_eq_class
class FeynmanIICh8Eq7(KnownEquation):
    """
    - Equation: II.8.7
    - Raw: 3 / 5 * q ** 2 / (4 * pi * 8.854e-12 * d)
    - Num. Vars: 2
    - Vars:
        - x[0]: q (float)
        - x[1]: d (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-ii.8.7'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e-12, 1.0e-10, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 3 / 5 * x[0] ** 2 / (4 * sympy.pi * ELECTRIC_CONSTANT * x[1])

    def eq_func(self, x):
        return 3 / 5 * x[0] ** 2 / (4 * np.pi * ELECTRIC_CONSTANT * x[1])


@register_feynman_eq_class
class FeynmanIICh8Eq31(KnownEquation):
    """
    - Equation: II.8.31
    - Raw: 8.854e-12 * Ef ** 2 / 2
    - Num. Vars: 1
    - Vars:
        - x[0]: Ef (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-ii.8.31'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e1, 1.0e3, uses_negative=False)]

        super().__init__(num_vars=1, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = ELECTRIC_CONSTANT * x[0] ** 2 / 2

    def eq_func(self, x):
        return ELECTRIC_CONSTANT * x[0] ** 2 / 2


@register_feynman_eq_class
class FeynmanIICh10Eq9(KnownEquation):
    """
    - Equation: II.10.9
    - Raw: sigma_den / 8.854e-12 * 1 / (1 + chi)
    - Num. Vars: 2
    - Vars:
        - x[0]: sigma_den (float)
        - x[1]: chi (float, positive)
    - Constraints:
        - 1 + x[1] != 0
    """
    _eq_name = 'feynman-ii.10.9'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0, 1.0e2, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / ELECTRIC_CONSTANT * 1 / (1 + x[1])

    def eq_func(self, x):
        return x[0] / ELECTRIC_CONSTANT * 1 / (1 + x[1])


@register_feynman_eq_class
class FeynmanIICh11Eq3(KnownEquation):
    """
    - Equation: II.11.3
    - Raw: q * Ef / (m * (omega_0 ** 2 - omega ** 2))
    - Num. Vars: 5
    - Vars:
        - x[0]: q (float)
        - x[1]: Ef (float, positive)
        - x[2]: m (float, positive)
        - x[3]: omega_0 (float)
        - x[4]: omega (float)
    - Constraints:
        - x[2] != 0
        - x[3] ** 2 - x[4] ** 2 != 0
    """
    _eq_name = 'feynman-ii.11.3'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e-9, 1.0e-7, uses_negative=False),
                DefaultSampling(1.0e-28, 1.0e-26, uses_negative=False), DefaultSampling(1.0e9, 1.0e11),
                DefaultSampling(1.0e9, 1.0e11)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / (x[2] * (x[3] ** 2 - x[4] ** 2))

    def eq_func(self, x):
        return x[0] * x[1] / (x[2] * (x[3] ** 2 - x[4] ** 2))


@register_feynman_eq_class
class FeynmanIICh11Eq17(KnownEquation):
    """
    - Equation: II.11.17
    - Raw: n_0 * (1 + p_d * Ef * cos(theta) / (1.380649e-23 * T))
    - Num. Vars: 5
    - Vars:
        - x[0]: n_0 (float, positive)
        - x[1]: p_d (float)
        - x[2]: Ef (float)
        - x[3]: theta (float)
        - x[4]: T (float, positive)
    - Constraints:
        - x[4] != 0
    """
    _eq_name = 'feynman-ii.11.17'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e27, 1.0e29, uses_negative=False), DefaultSampling(1.0e-22, 1.0e-20),
                DefaultSampling(1.0e1, 1.0e3), SimpleSampling(0, 2 * np.pi, uses_negative=False),
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (1 + x[1] * x[2] * sympy.cos(x[3]) / (BOLTZMANN_CONSTANT * x[4]))

    def eq_func(self, x):
        return x[0] * (1 + x[1] * x[2] * np.cos(x[3]) / (BOLTZMANN_CONSTANT * x[4]))


@register_feynman_eq_class
class FeynmanIICh11Eq20(KnownEquation):
    """
    - Equation: II.11.20
    - Raw: n_rho * p_d ** 2 * Ef / (3 * 1.380649e-23 * T)
    - Num. Vars: 4
    - Vars:
        - x[0]: n_rho (integer -> real due to its order, positive)
        - x[1]: p_d (float)
        - x[2]: Ef (float)
        - x[3]: T (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-ii.11.20'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False), DefaultSampling(1.0e-22, 1.0e-20),
                DefaultSampling(1.0e1, 1.0e3), DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] ** 2 * x[2] / (3 * BOLTZMANN_CONSTANT * x[3])

    def eq_func(self, x):
        return x[0] * x[1] ** 2 * x[2] / (3 * BOLTZMANN_CONSTANT * x[3])


@register_feynman_eq_class
class FeynmanIICh11Eq27(KnownEquation):
    """
    - Equation: II.11.27
    - Raw: n * alpha / (1 - (n * alpha / 3)) * 8.854e-12 * Ef
    - Num. Vars: 3
    - Vars:
        - x[0]: n (integer -> real due to its order, positive)
        - x[1]: alpha (float, positive)
        - x[2]: Ef (float, positive)
    - Constraints:
        - 1 - (x[0] * x[1] / 3) != 0
    """
    _eq_name = 'feynman-ii.11.27'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e-33, 1.0e-31, uses_negative=False),
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / (1 - (x[0] * x[1] / 3)) * ELECTRIC_CONSTANT * x[2]

    def eq_func(self, x):
        return x[0] * x[1] / (1 - (x[0] * x[1] / 3)) * ELECTRIC_CONSTANT * x[2]


@register_feynman_eq_class
class FeynmanIICh11Eq28(KnownEquation):
    """
    - Equation: II.11.28
    - Raw: 1 + n * alpha / (1 - (n * alpha / 3))
    - Num. Vars: 2
    - Vars:
        - x[0]: n (integer -> real due to its order, positive)
        - x[1]: alpha (float, positive)
    - Constraints:
        - 1-(x[0]*x[1]/3) != 0
    """
    _eq_name = 'feynman-ii.11.28'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e-33, 1.0e-31, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 + x[0] * x[1] / (1 - (x[0] * x[1] / 3))

    def eq_func(self, x):
        return 1 + x[0] * x[1] / (1 - (x[0] * x[1] / 3))


@register_feynman_eq_class
class FeynmanIICh13Eq17(KnownEquation):
    """
    - Equation: II.13.17
    - Raw: 1 / (4 * pi * 8.854e-12 * 2.99792458e8 ** 2) * 2 * I / r
    - Num. Vars: 2
    - Vars:
        - x[0]: I (float)
        - x[1]: r (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-ii.13.17'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (4 * sympy.pi * ELECTRIC_CONSTANT * SPEED_OF_LIGHT ** 2) * 2 * x[0] / x[1]

    def eq_func(self, x):
        return 1 / (4 * np.pi * ELECTRIC_CONSTANT * SPEED_OF_LIGHT ** 2) * 2 * x[0] / x[1]


@register_feynman_eq_class
class FeynmanIICh13Eq23(KnownEquation):
    """
    - Equation: II.13.23
    - Raw: rho_c_0 / sqrt(1 - v ** 2 / 2.99792458e8 ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: rho_c_0 (float, positive)
        - x[1]: v (float, positive)
    - Constraints:
        - 2.99792458e8 ** 2 - x[1] ** 2 > 0
    """
    _eq_name = 'feynman-ii.13.23'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e27, 1.0e29, uses_negative=False),
                DefaultSampling(1.0e6, 1.0e8, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / sympy.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return x[0] / np.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanIICh13Eq34(KnownEquation):
    """
    - Equation: II.13.34
    - Raw: rho_c_0 * v / sqrt(1 - v ** 2 / 2.99792458e8 ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: rho_c_0 (float, positive)
        - x[1]: v (float, positive)
    - Constraints:
        - 2.99792458e8 ** 2 - x[1] ** 2 > 0
    """
    _eq_name = 'feynman-ii.13.34'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e27, 1.0e29, uses_negative=False),
                DefaultSampling(1.0e6, 1.0e8, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / sympy.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)

    def eq_func(self, x):
        return x[0] * x[1] / np.sqrt(1 - x[1] ** 2 / SPEED_OF_LIGHT ** 2)


@register_feynman_eq_class
class FeynmanIICh15Eq4(KnownEquation):
    """
    - Equation: II.15.4
    - Raw: -mom * B * cos(theta)
    - Num. Vars: 3
    - Vars:
        - x[0]: mom (float)
        - x[1]: B (float)
        - x[2]: theta (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-ii.15.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-25, 1.0e-23), DefaultSampling(1.0e-3, 1.0e-1),
                SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = -x[0] * x[1] * sympy.cos(x[2])

    def eq_func(self, x):
        return -x[0] * x[1] * np.cos(x[2])


@register_feynman_eq_class
class FeynmanIICh15Eq5(KnownEquation):
    """
    - Equation: II.15.5
    - Raw: -p_d * Ef * cos(theta)
    - Num. Vars: 3
    - Vars:
        - x[0]: p_d (float)
        - x[1]: Ef (float)
        - x[2]: theta (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-ii.15.5'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-22, 1.0e-20), DefaultSampling(1.0e1, 1.0e3),
                SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = -x[0] * x[1] * sympy.cos(x[2])

    def eq_func(self, x):
        return -x[0] * x[1] * np.cos(x[2])


@register_feynman_eq_class
class FeynmanIICh21Eq32(KnownEquation):
    """
    - Equation: II.21.32
    - Raw: q / (4 * pi * 8.854e-12 * r * (1 - v / 2.99792458e8))
    - Num. Vars: 3
    - Vars:
        - x[0]: q (float)
        - x[1]: r (float, positive)
        - x[2]: v (float, positive)
    - Constraints:
        - x[1] != 0
        - 2.99792458e8 - x[2] > 0
    """
    _eq_name = 'feynman-ii.21.32'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0, 1.0e2, uses_negative=False),
                DefaultSampling(1.0e6, 1.0e8, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (4 * sympy.pi * ELECTRIC_CONSTANT * x[1] * (1 - x[2] / SPEED_OF_LIGHT))

    def eq_func(self, x):
        return x[0] / (4 * np.pi * ELECTRIC_CONSTANT * x[1] * (1 - x[2] / SPEED_OF_LIGHT))


@register_feynman_eq_class
class FeynmanIICh24Eq17(KnownEquation):
    """
    - Equation: II.24.17
    - Raw: sqrt(omega ** 2 / 2.99792458e8 ** 2 - pi ** 2 / d ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: omega (float)
        - x[1]: d (float, positive)
    - Constraints:
        - x[0] ** 2 / 2.99792458e8 ** 2 - np.pi ** 2 / x[1] ** 2 >= 0
        - x[1] != 0
    """
    _eq_name = 'feynman-ii.24.17'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e9, 1.0e11), DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt(x[0] ** 2 / SPEED_OF_LIGHT ** 2 - sympy.pi ** 2 / x[1] ** 2)

    def eq_func(self, x):
        return np.sqrt(x[0] ** 2 / SPEED_OF_LIGHT ** 2 - np.pi ** 2 / x[1] ** 2)


@register_feynman_eq_class
class FeynmanIICh27Eq16(KnownEquation):
    """
    - Equation: II.27.16
    - Raw: 8.854e-12 * 2.99792458e8 * Ef ** 2
    - Num. Vars: 1
    - Vars:
        - x[0]: Ef (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-ii.27.16'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)]

        super().__init__(num_vars=1, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = ELECTRIC_CONSTANT * SPEED_OF_LIGHT * x[0] ** 2

    def eq_func(self, x):
        return ELECTRIC_CONSTANT * SPEED_OF_LIGHT * x[0] ** 2


@register_feynman_eq_class
class FeynmanIICh27Eq18(KnownEquation):
    """
    - Equation: II.27.18
    - Raw: 8.854e-12 * Ef ** 2
    - Num. Vars: 1
    - Vars:
        - x[0]: Ef (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-ii.27.18'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)]

        super().__init__(num_vars=1, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = ELECTRIC_CONSTANT * x[0] ** 2

    def eq_func(self, x):
        return ELECTRIC_CONSTANT * x[0] ** 2


@register_feynman_eq_class
class FeynmanIICh34Eq2a(KnownEquation):
    """
    - Equation: II.34.2a
    - Raw: q * v / (2 * pi * r)
    - Num. Vars: 3
    - Vars:
        - x[0]: q (float)
        - x[1]: v (float)
        - x[2]: r (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-ii.34.2a'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e5, 1.0e7),
                DefaultSampling(1.0e-11, 1.0e-9, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / (2 * sympy.pi * x[2])

    def eq_func(self, x):
        return x[0] * x[1] / (2 * np.pi * x[2])


@register_feynman_eq_class
class FeynmanIICh34Eq2(KnownEquation):
    """
    - Equation: II.34.2
    - Raw: q * v * r / 2
    - Num. Vars: 3
    - Vars:
        - x[0]: q (float)
        - x[1]: v (float)
        - x[2]: r (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-ii.34.2'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e5, 1.0e7),
                DefaultSampling(1.0e-11, 1.0e-9, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * x[2] / 2

    def eq_func(self, x):
        return x[0] * x[1] * x[2] / 2


@register_feynman_eq_class
class FeynmanIICh34Eq11(KnownEquation):
    """
    - Equation: II.34.11
    - Raw: g_ * q * B / (2 * m)
    - Num. Vars: 4
    - Vars:
        - x[0]: g_ (float)
        - x[1]: q (float)
        - x[2]: B (float)
        - x[3]: m (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-ii.34.11'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                SimpleSampling(-1.0, 1.0, uses_negative=False),
                DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e-9, 1.0e-7),
                DefaultSampling(1.0e-30, 1.0e-28, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * x[2] / (2 * x[3])

    def eq_func(self, x):
        return x[0] * x[1] * x[2] / (2 * x[3])


@register_feynman_eq_class
class FeynmanIICh34Eq29a(KnownEquation):
    """
    - Equation: II.34.29a
    - Raw: q * 6.626e-34 / (4 * pi * m)
    - Num. Vars: 2
    - Vars:
        - x[0]: q (float)
        - x[1]: m (float, positive)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-ii.34.29a'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e-30, 1.0e-28, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * PLANCK_CONSTANT / (4 * sympy.pi * x[1])

    def eq_func(self, x):
        return x[0] * PLANCK_CONSTANT / (4 * np.pi * x[1])


@register_feynman_eq_class
class FeynmanIICh34Eq29b(KnownEquation):
    """
    - Equation: II.34.29b
    - Raw: g_ * 9.2740100783e-24 * B * Jz / (6.626e-34 / (2 * pi))
    - Num. Vars: 3
    - Vars:
        - x[0]: g_ (float)
        - x[1]: B (float)
        - x[2]: Jz (float)
    - Constraints:
    """
    _eq_name = 'feynman-ii.34.29b'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                SimpleSampling(-1.0, 1.0, uses_negative=False),
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-26, 1.0e-22)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * BOHR_MAGNETON * x[1] * x[2] / (PLANCK_CONSTANT / (2 * sympy.pi))

    def eq_func(self, x):
        return x[0] * BOHR_MAGNETON * x[1] * x[2] / (PLANCK_CONSTANT / (2 * np.pi))


@register_feynman_eq_class
class FeynmanIICh35Eq18(KnownEquation):
    """
    - Equation: II.35.18
    - Raw: n_0 / (exp(mom * B / (1.380649e-23 * T)) + exp(-mom * B / (1.380649e-23 * T)))
    - Num. Vars: 4
    - Vars:
        - x[0]: n_0 (integer -> real due to its order, positive)
        - x[1]: mom (float, positive)
        - x[2]: B (float, positive)
        - x[3]: T (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-ii.35.18'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e-25, 1.0e-23, uses_negative=False),
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False), DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (sympy.exp(x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3]))
                                + sympy.exp(-x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3])))

    def eq_func(self, x):
        return x[0] / (np.exp(x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3]))
                       + np.exp(-x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3])))


@register_feynman_eq_class
class FeynmanIICh35Eq21(KnownEquation):
    """
    - Equation: II.35.21
    - Raw: n_rho * mom * tanh(mom * B / (1.380649e-23 * T))
    - Num. Vars: 4
    - Vars:
        - x[0]: n_rho (integer -> real due to its order, positive)
        - x[1]: mom (float, positive)
        - x[2]: B (float, positive)
        - x[3]: T (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-ii.35.21'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e-25, 1.0e-23, uses_negative=False),
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False), DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * sympy.tanh(x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3]))

    def eq_func(self, x):
        return x[0] * x[1] * np.tanh(x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3]))


@register_feynman_eq_class
class FeynmanIICh36Eq38(KnownEquation):
    """
    - Equation: II.36.38
    - Raw: mom * H / (1.380649e-23 * T) + (mom * alpha) / (8.854e-12 * 2.99792458e8 ** 2 * 1.380649e-23 * T) * M
    - Num. Vars: 5
    - Vars:
        - x[0]: mom (float)
        - x[1]: H (float)
        - x[2]: T (float, positive)
        - x[3]: alpha (float, positive)
        - x[4]: M (integer -> real due to its order, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-ii.36.38'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-25, 1.0e-23), DefaultSampling(1.0e-3, 1.0e-1),
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False), SimpleSampling(0, 1, uses_negative=False),
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / (BOLTZMANN_CONSTANT * x[2]) + (x[0] * x[3]) / (ELECTRIC_CONSTANT * SPEED_OF_LIGHT ** 2 * BOLTZMANN_CONSTANT * x[2]) * x[4]

    def eq_func(self, x):
        return x[0] * x[1] / (BOLTZMANN_CONSTANT * x[2]) + (x[0] * x[3]) / (ELECTRIC_CONSTANT * SPEED_OF_LIGHT ** 2 * BOLTZMANN_CONSTANT * x[2]) * x[4]


@register_feynman_eq_class
class FeynmanIICh37Eq1(KnownEquation):
    """
    - Equation: II.37.1
    - Raw: mom * (1 + chi) * B
    - Num. Vars: 3
    - Vars:
        - x[0]: mom (float)
        - x[1]: chi (float)
        - x[2]: B (float)
    - Constraints:
    """
    _eq_name = 'feynman-ii.37.1'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-25, 1.0e-23), DefaultSampling(1.0e4, 1.0e6),
                DefaultSampling(1.0e-3, 1.0e-1)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (1 + x[1]) * x[2]

    def eq_func(self, x):
        return x[0] * (1 + x[1]) * x[2]


@register_feynman_eq_class
class FeynmanIICh38Eq3(KnownEquation):
    """
    - Equation: II.38.3
    - Raw: Y * A * x / d
    - Num. Vars: 4
    - Vars:
        - x[0]: Y (float, positive)
        - x[1]: A (float, positive)
        - x[2]: x (float)
        - x[3]: d (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-ii.38.3'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-4, 1.0e-2, uses_negative=False),
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-2, 1.0, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] * x[2] / x[3]

    def eq_func(self, x):
        return x[0] * x[1] * x[2] / x[3]


@register_feynman_eq_class
class FeynmanIICh38Eq14(KnownEquation):
    """
    - Equation: II.38.14
    - Raw: Y / (2 * (1 + sigma))
    - Num. Vars: 2
    - Vars:
        - x[0]: Y (float, positive)
        - x[1]: sigma (float)
    - Constraints:
        - 1 + x[1] != 0
    """
    _eq_name = 'feynman-ii.38.14'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-2, 1.0, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (2 * (1 + x[1]))

    def eq_func(self, x):
        return x[0] / (2 * (1 + x[1]))


@register_feynman_eq_class
class FeynmanIIICh4Eq32(KnownEquation):
    """
    - Equation: III.4.32
    - Raw: 1 / (exp((6.626e-34 / (2 * pi)) * omega / (1.380649e-23 * T)) - 1)
    - Num. Vars: 2
    - Vars:
        - x[0]: omega (float, positive)
        - x[1]: T (float, positive)
    - Constraints:
        - x[0] != 0
        - x[1] != 0
    """
    _eq_name = 'feynman-iii.4.32'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False),
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (sympy.exp((PLANCK_CONSTANT / (2 * sympy.pi)) * x[0] / (BOLTZMANN_CONSTANT * x[1])) - 1)

    def eq_func(self, x):
        return 1 / (np.exp((PLANCK_CONSTANT / (2 * np.pi)) * x[0] / (BOLTZMANN_CONSTANT * x[1])) - 1)


@register_feynman_eq_class
class FeynmanIIICh4Eq33(KnownEquation):
    """
    - Equation: III.4.33
    - Raw: (6.626e-34 / (2 * pi)) * omega / (exp((6.626e-34 / (2 * pi)) * omega / (1.380649e-23 * T)) - 1)
    - Num. Vars: 2
    - Vars:
        - x[0]: omega (float, positive)
        - x[1]: T (float, positive)
    - Constraints:
        - x[0] != 0
        - x[1] != 0
    """
    _eq_name = 'feynman-iii.4.33'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False),
                DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (PLANCK_CONSTANT / (2 * sympy.pi)) * x[0] / (sympy.exp((PLANCK_CONSTANT / (2 * sympy.pi)) * x[0] / (BOLTZMANN_CONSTANT * x[1])) - 1)

    def eq_func(self, x):
        return (PLANCK_CONSTANT / (2 * np.pi)) * x[0] / (np.exp((PLANCK_CONSTANT / (2 * np.pi)) * x[0] / (BOLTZMANN_CONSTANT * x[1])) - 1)


@register_feynman_eq_class
class FeynmanIIICh7Eq38(KnownEquation):
    """
    - Equation: III.7.38
    - Raw: 2 * mom * B / (6.626e-34 / (2 * pi))
    - Num. Vars: 2
    - Vars:
        - x[0]: mom (float)
        - x[1]: B (float)
    - Constraints:
    """
    _eq_name = 'feynman-iii.7.38'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-11, 1.0e-9), DefaultSampling(1.0e-3, 1.0e-1)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 2 * x[0] * x[1] / (PLANCK_CONSTANT / (2 * sympy.pi))

    def eq_func(self, x):
        return 2 * x[0] * x[1] / (PLANCK_CONSTANT / (2 * np.pi))


@register_feynman_eq_class
class FeynmanIIICh8Eq54(KnownEquation):
    """
    - Equation: III.8.54
    - Raw: sin(E_n * t / (6.626e-34 / (2 * pi))) ** 2
    - Num. Vars: 2
    - Vars:
        - x[0]: E_n (float)
        - x[1]: t (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-iii.8.54'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-18, 1.0e-16), DefaultSampling(1.0e-18, 1.0e-16, uses_negative=False)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sin(x[0] * x[1] / (PLANCK_CONSTANT / (2 * sympy.pi))) ** 2

    def eq_func(self, x):
        return np.sin(x[0] * x[1] / (PLANCK_CONSTANT / (2 * np.pi))) ** 2


@register_feynman_eq_class
class FeynmanIIICh9Eq52(KnownEquation):
    """
    - Equation: III.9.52
    - Raw: (p_d * Ef * t / (6.626e-34 / (2 * pi))) ** 2 * sin((omega - omega_0) * t / 2) ** 2 / ((omega - omega_0) * t / 2) ** 2
    - Num. Vars: 5
    - Vars:
        - x[0]: p_d (float)
        - x[1]: Ef (float)
        - x[2]: t (float, positive)
        - x[3]: omega (float, positive)
        - x[4]: omega_0 (float, positive)
    - Constraints:
        - x[2] != 0
        - x[3] - x[4] != 0
    """
    _eq_name = 'feynman-iii.9.52'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-22, 1.0e-20), DefaultSampling(1.0e1, 1.0e3),
                DefaultSampling(1.0e-18, 1.0e-16, uses_negative=False),
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False), DefaultSampling(1.0e8, 1.0e10, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (x[0] * x[1] * x[2] / (PLANCK_CONSTANT / (2 * sympy.pi))) * sympy.sin((x[3] - x[4]) * x[2] / 2) ** 2 / ((x[3] - x[4]) * x[2] / 2) ** 2

    def eq_func(self, x):
        return (x[0] * x[1] * x[2] / (PLANCK_CONSTANT / (2 * np.pi))) ** 2 * np.sin((x[3] - x[4]) * x[2] / 2) ** 2 / ((x[3] - x[4]) * x[2] / 2) ** 2


@register_feynman_eq_class
class FeynmanIIICh10Eq19(KnownEquation):
    """
    - Equation: III.10.19
    - Raw: mom * sqrt(Bx ** 2 + By ** 2 + Bz ** 2)
    - Num. Vars: 4
    - Vars:
        - x[0]: mom (float)
        - x[1]: Bx (float)
        - x[2]: By (float)
        - x[3]: Bz (float)
    - Constraints:
    """
    _eq_name = 'feynman-iii.10.19'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-25, 1.0e-23), DefaultSampling(1.0e-3, 1.0e-1),
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-3, 1.0e-1)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * sympy.sqrt(x[1] ** 2 + x[2] ** 2 + x[3] ** 2)

    def eq_func(self, x):
        return x[0] * np.sqrt(x[1] ** 2 + x[2] ** 2 + x[3] ** 2)


@register_feynman_eq_class
class FeynmanIIICh12Eq43(KnownEquation):
    """
    - Equation: III.12.43
    - Raw: n * (6.626e-34 / (2 * pi))
    - Num. Vars: 1
    - Vars:
        - x[0]: n (integer)
    - Constraints:
    """
    _eq_name = 'feynman-iii.12.43'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [IntegerSampling(1, 1.0e2, uses_negative=False)]

        super().__init__(num_vars=1, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (PLANCK_CONSTANT / (2 * sympy.pi))

    def eq_func(self, x):
        return x[0] * (PLANCK_CONSTANT / (2 * np.pi))


@register_feynman_eq_class
class FeynmanIIICh13Eq18(KnownEquation):
    """
    - Equation: III.13.18
    - Raw: 2 * E_n * d ** 2 * k / (6.626e-34 / (2 * pi))
    - Num. Vars: 3
    - Vars:
        - x[0]: E_n (float)
        - x[1]: d (float, positive)
        - x[2]: k (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-iii.13.18'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-18, 1.0e-16), DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 2 * x[0] * x[1] ** 2 * x[2] / (PLANCK_CONSTANT / (2 * sympy.pi))

    def eq_func(self, x):
        return 2 * x[0] * x[1] ** 2 * x[2] / (PLANCK_CONSTANT / (2 * np.pi))


@register_feynman_eq_class
class FeynmanIIICh14Eq14(KnownEquation):
    """
    - Equation: III.14.14
    - Raw: I_0 * (exp(q * Volt / (1.380649e-23 * T)) - 1)
    - Num. Vars: 4
    - Vars:
        - x[0]: I_0 (float)
        - x[1]: q (float, positive)
        - x[2]: Volt (float)
        - x[3]: T (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-iii.14.14'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-22, 1.0e-20, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e1, 1.0e3, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (sympy.exp(x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3])) - 1)

    def eq_func(self, x):
        return x[0] * (np.exp(x[1] * x[2] / (BOLTZMANN_CONSTANT * x[3])) - 1)


@register_feynman_eq_class
class FeynmanIIICh15Eq12(KnownEquation):
    """
    - Equation: III.15.12
    - Raw: 2 * U * (1 - cos(k * d))
    - Num. Vars: 3
    - Vars:
        - x[0]: U (float, positive)
        - x[1]: k (float, positive)
        - x[2]: d (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-iii.15.12'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-18, 1.0e-16, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 2 * x[0] * (1 - sympy.cos(x[1] * x[2]))

    def eq_func(self, x):
        return 2 * x[0] * (1 - np.cos(x[1] * x[2]))


@register_feynman_eq_class
class FeynmanIIICh15Eq14(KnownEquation):
    """
    - Equation: III.15.14
    - Raw: (6.626e-34 / (2 * pi)) ** 2 / (2 * E_n * d ** 2)
    - Num. Vars: 2
    - Vars:
        - x[0]: E_n (float, positive)
        - x[1]: d (float, positive)
    - Constraints:
        - x[0] != 0
        - x[1] != 0
    """
    _eq_name = 'feynman-iii.15.14'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-18, 1.0e-16, uses_negative=False),
                DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (PLANCK_CONSTANT / (2 * sympy.pi)) ** 2 / (2 * x[0] * x[1] ** 2)

    def eq_func(self, x):
        return (PLANCK_CONSTANT / (2 * np.pi)) ** 2 / (2 * x[0] * x[1] ** 2)


@register_feynman_eq_class
class FeynmanIIICh15Eq27(KnownEquation):
    """
    - Equation: III.15.27
    - Raw: 2 * pi * alpha / (n * d)
    - Num. Vars: 3
    - Vars:
        - x[0]: alpha (integer)
        - x[1]: n (integer, positive)
        - x[2]: d (float, positive)
    - Constraints:
        - x[1] != 0
        - x[2] != 0
    """
    _eq_name = 'feynman-iii.15.27'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                IntegerSampling(1, 1.0e2), IntegerSampling(1, 1.0e2, uses_negative=False),
                DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 2 * sympy.pi * x[0] / (x[1] * x[2])

    def eq_func(self, x):
        return 2 * np.pi * x[0] / (x[1] * x[2])


@register_feynman_eq_class
class FeynmanIIICh17Eq37(KnownEquation):
    """
    - Equation: III.17.37
    - Raw: beta * (1 + alpha * cos(theta))
    - Num. Vars: 3
    - Vars:
        - x[0]: beta (float, positive)
        - x[1]: alpha (float)
        - x[2]: theta (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-iii.17.37'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-18, 1.0e-16, uses_negative=False), DefaultSampling(1.0e-18, 1.0e-16),
                SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (1 + x[1] * sympy.cos(x[2]))

    def eq_func(self, x):
        return x[0] * (1 + x[1] * np.cos(x[2]))


@register_feynman_eq_class
class FeynmanIIICh19Eq51(KnownEquation):
    """
    - Equation: III.19.51
    - Raw: -m * q ** 4 / (2 * (4 * pi * 8.854e-12) ** 2 * (6.626e-34 / (2 * pi)) ** 2) * (1 / n ** 2)
    - Num. Vars: 3
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: q (float)
        - x[2]: n (integer, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-iii.19.51'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-30, 1.0e-28, uses_negative=False), DefaultSampling(1.0e-11, 1.0e-9),
                IntegerSampling(1, 1.0e2, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = -x[0] * x[1] ** 4 / (2 * (4 * sympy.pi * ELECTRIC_CONSTANT) ** 2 * (PLANCK_CONSTANT / (2 * sympy.pi)) ** 2) * (1 / x[2] ** 2)

    def eq_func(self, x):
        return -x[0] * x[1] ** 4 / (2 * (4 * np.pi * ELECTRIC_CONSTANT) ** 2 * (PLANCK_CONSTANT / (2 * np.pi)) ** 2) * (1 / x[2] ** 2)


@register_feynman_eq_class
class FeynmanIIICh21Eq20(KnownEquation):
    """
    - Equation: III.21.20
    - Raw: -rho_c_0 * q * A_vec / m
    - Num. Vars: 4
    - Vars:
        - x[0]: rho_c_0 (float)
        - x[1]: q (float, positive)
        - x[2]: A_vec (float)
        - x[3]: m (float, positive)
    - Constraints:
        - x[3] != 0
    """
    _eq_name = 'feynman-iii.21.20'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-29, 1.0e-27, uses_positive=False),
                DefaultSampling(1.0e-11, 1.0e-9, uses_positive=False),
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-30, 1.0e-28, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = -x[0] * x[1] * x[2] / x[3]

    def eq_func(self, x):
        return -x[0] * x[1] * x[2] / x[3]


@register_feynman_eq_class
class FeynmanBonus1(KnownEquation):
    """
    - Equation: Rutherford scattering
    - Raw: (Z_1 * Z_2 * alpha * 1.054571817e-34 * 2.99792458e8 / (4 * E_n * sin(theta / 2) ** 2)) ** 2
    - Num. Vars: 4
    - Vars:
        - x[0]: Z_1 (integer, positive)
        - x[1]: Z_2 (integer, positive)
        - x[2]: E_n (float, positive)
        - x[3]: theta (float, positive)
    - Constraints:
        - x[2] != 0
        - np.sin(x[3] / 2) != 0
    """
    _eq_name = 'feynman-bonus.1'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                IntegerSampling(1.0, 1.0e1, uses_negative=False), IntegerSampling(1.0, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-18, 1.0e-16, uses_negative=False),
                SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (x[0] * x[1] * FINE_STRUCTURE_CONSTANT * DIRAC_CONSTANT * SPEED_OF_LIGHT
                         / (4 * x[2] * sympy.sin(x[3] / 2) ** 2)) ** 2

    def eq_func(self, x):
        return (x[0] * x[1] * FINE_STRUCTURE_CONSTANT * DIRAC_CONSTANT * SPEED_OF_LIGHT
                / (4 * x[2] * np.sin(x[3] / 2) ** 2)) ** 2


@register_feynman_eq_class
class FeynmanBonus2(KnownEquation):
    """
    - Equation: 3.55 Goldstein
    - Raw: m * k_G / L ** 2 * (1 + sqrt(1 + 2 * E_n * L ** 2 / (m * k_G ** 2)) * cos(theta1 - theta2))
    - Num. Vars: 6
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: k_G (float, positive)
        - x[2]: L (float, positive)
        - x[3]: E_n (float, positive)
        - x[4]: theta1 (float, positive)
        - x[5]: theta2 (float, positive)
    - Constraints:
        - x[0] != 0
        - x[1] != 0
        - x[3] * x[2] ** 2 / (x[0] * x[1] ** 2) >= -1 / 2
    """
    _eq_name = 'feynman-bonus.2'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e9, 1.0e11, uses_negative=False),
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False),
                DefaultSampling(1.0e25, 1.0e27, uses_negative=False),
                SimpleSampling(0, 2 * np.pi, uses_negative=False), SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=6, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * x[1] / x[2] ** 2 * (1 + sympy.sqrt(1 + 2 * x[3] * x[2] ** 2 / (x[0] * x[1] ** 2)) * sympy.cos(x[4] - x[5]))

    def eq_func(self, x):
        return x[0] * x[1] / x[2] ** 2 * (1 + np.sqrt(1 + 2 * x[3] * x[2] ** 2 / (x[0] * x[1] ** 2)) * np.cos(x[4] - x[5]))


@register_feynman_eq_class
class FeynmanBonus3(KnownEquation):
    """
    - Equation: 3.64 Goldstein
    - Raw: d * (1 - alpha ** 2) / (1 + alpha * cos(theta1 - theta2))
    - Num. Vars: 4
    - Vars:
        - x[0]: d (float, positive)
        - x[1]: alpha (float, positive)
        - x[2]: theta1 (float, positive)
        - x[3]: theta2 (float, positive)
    - Constraints:
        - x[1] * np.cos(x[2] - x[3]) != -1
    """
    _eq_name = 'feynman-bonus.3'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False), SimpleSampling(0.0, 1.0, uses_negative=False),
                SimpleSampling(0, 2 * np.pi, uses_negative=False), SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (1 - x[1] ** 2) / (1 + x[1] * sympy.cos(x[2] - x[3]))

    def eq_func(self, x):
        return x[0] * (1 - x[1] ** 2) / (1 + x[1] * np.cos(x[2] - x[3]))


@register_feynman_eq_class
class FeynmanBonus4(KnownEquation):
    """
    - Equation: 3.16 Goldstein
    - Raw: sqrt(2 / m * (E_n - U - L ** 2 / (2 * m * r ** 2)))
    - Num. Vars: 5
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: E_n (float, positive)
        - x[2]: U (float, positive)
        - x[3]: L (float, positive)
        - x[4]: r (float, positive)
    - Constraints:
        - 2 / x[0] * (x[1] - x[2] - x[3] ** 2 / (2 * x[0] * x[4] ** 2)) >= 0
        - x[0] != 0
        - x[4] != 0
    """
    _eq_name = 'feynman-bonus.4'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e25, 1.0e27, uses_negative=False),
                DefaultSampling(1.0e25, 1.0e27, uses_negative=False), DefaultSampling(1.0e8, 1.0e10),
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt(2 / x[0] * (x[1] - x[2] - x[3] ** 2 / (2 * x[0] * x[4] ** 2)))

    def eq_func(self, x):
        return np.sqrt(2 / x[0] * (x[1] - x[2] - x[3] ** 2 / (2 * x[0] * x[4] ** 2)))


@register_feynman_eq_class
class FeynmanBonus5(KnownEquation):
    """
    - Equation: 3.74 Goldstein
    - Raw: 2 * pi * d ** (3 / 2) / sqrt(6.67430e-11 * (m1 + m2))
    - Num. Vars: 3
    - Vars:
        - x[0]: d (float, positive)
        - x[2]: m1 (float, positive)
        - x[3]: m2 (float, positive)
    - Constraints:
        - x[1] != 0
        - x[2] + x[3] != 0
        - x[1] * (x[2] + x[3]) > 0
    """
    _eq_name = 'feynman-bonus.5'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False),
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 2 * sympy.pi * x[0] ** (3 / 2) / sympy.sqrt(GRAVITATIONAL_CONSTANT * (x[1] + x[2]))

    def eq_func(self, x):
        return 2 * np.pi * x[0] ** (3 / 2) / np.sqrt(GRAVITATIONAL_CONSTANT * (x[1] + x[2]))


@register_feynman_eq_class
class FeynmanBonus6(KnownEquation):
    """
    - Equation: 3.99 Goldstein
    - Raw: sqrt(1 + 2 * epsilon ** 2 * E_n * L ** 2 / (m * (Z_1 * Z_2 * q ** 2) ** 2))
    - Python:
    - Num. Vars: 7
    - Vars:
        - x[0]: epsilon (float)
        - x[1]: E_n (float, positive)
        - x[2]: L (float, positive)
        - x[3]: m (float, positive)
        - x[4]: Z_1 (integer, positive)
        - x[5]: Z_2 (integer, positive)
        - x[6]: q (float)
    - Constraints:
        - x[3] != 0
        - x[4] != 0
        - x[5] != 0
        - x[6] != 0
        - 1 + 2 * x[0] * x[1] * x[2] ** 2 / (x[3] * (x[4] * x[5] * x[6] ** 2) ** 2) >= 0
    """
    _eq_name = 'feynman-bonus.6'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-18, 1.0e-16), DefaultSampling(1.0e-18, 1.0e-16, uses_negative=False),
                DefaultSampling(1.0e-10, 1.0e-8, uses_negative=False),
                DefaultSampling(1.0e-30, 1.0e-28, uses_negative=False),
                IntegerSampling(1.0, 1.0e1, uses_negative=False), IntegerSampling(1.0, 1.0e1, uses_negative=False),
                DefaultSampling(1.0e-11, 1.0e-9)
            ]

        super().__init__(num_vars=7, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt(1 + 2 * x[0] * x[1] * x[2] ** 2 / (x[3] * (x[4] * x[5] * x[6] ** 2) ** 2))

    def eq_func(self, x):
        return np.sqrt(1 + 2 * x[0] * x[1] * x[2] ** 2 / (x[3] * (x[4] * x[5] * x[6] ** 2) ** 2))


@register_feynman_eq_class
class FeynmanBonus7(KnownEquation):
    """
    - Equation: Friedman Equation
    - Raw: sqrt(8 * pi * 6.67430e-11 * rho / 3 - alpha * 2.99792458e8 ** 2 / d ** 2)
    - Num. Vars: 3
    - Vars:
        - x[0]: rho (float, positive)
        - x[1]: alpha (Integer)
        - x[2]: d (float, positive)
    - Constraints:
        - x[2] != 0
        - 6.67430e-11 * x[0] * x[2] ** 2 / 3 >= x[1] * 2.99792458e8 ** 2
    """
    _eq_name = 'feynman-bonus.7'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-28, 1.0e-26, uses_negative=False), IntegerSampling(-1.0, 2.0),
                DefaultSampling(1.0e25, 1.0e27, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt(8 * sympy.pi * GRAVITATIONAL_CONSTANT * x[0] / 3 - x[1] * SPEED_OF_LIGHT ** 2 / x[2] ** 2)

    def eq_func(self, x):
        return np.sqrt(8 * np.pi * GRAVITATIONAL_CONSTANT * x[0] / 3 - x[1] * SPEED_OF_LIGHT ** 2 / x[2] ** 2)


@register_feynman_eq_class
class FeynmanBonus8(KnownEquation):
    """
    - Equation: Compton Scattering
    - Raw: E_n / (1 + E_n / (9.10938356e-31 * 2.99792458e8 ** 2) * (1 - cos(theta)))
    - Num. Vars: 2
    - Vars:
        - x[0]: E_n (float, positive)
        - x[1]: theta (float)
    - Constraints:
        - x[0] * (1 - np.cos(x[1])) / (9.10938356e-31 * 2.99792458e8 ** 2) != -1
    """
    _eq_name = 'feynman-bonus.8'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [DefaultSampling(1.0e-24, 1.0e-22, uses_negative=False), SimpleSampling(-np.pi, np.pi)]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (1 + x[0] / (ELECTRON_MASS * SPEED_OF_LIGHT ** 2) * (1 - sympy.cos(x[1])))

    def eq_func(self, x):
        return x[0] / (1 + x[0] / (ELECTRON_MASS * SPEED_OF_LIGHT ** 2) * (1 - np.cos(x[1])))


@register_feynman_eq_class
class FeynmanBonus9(KnownEquation):
    """
    - Equation: Gravitational wave ratiated power
    - Raw: -32/5 * 6.67430e-11 ** 4 / 2.99792458e8 ** 5 * (m1 * m2) ** 2 * (m1 + m2) / r ** 5
    - Num. Vars: 3
    - Vars:
        - x[0]: m1 (float, positive)
        - x[1]: m2 (float, positive)
        - x[2]: r (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-bonus.9'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e23, 1.0e25, uses_negative=False),
                DefaultSampling(1.0e8, 1.0e10, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = -32 / 5 * GRAVITATIONAL_CONSTANT ** 4 / SPEED_OF_LIGHT ** 5 * (x[0] * x[1]) ** 2 * (x[0] + x[1]) / x[2] ** 5

    def eq_func(self, x):
        return -32 / 5 * GRAVITATIONAL_CONSTANT ** 4 / SPEED_OF_LIGHT ** 5 * (x[0] * x[1]) ** 2 * (x[0] + x[1]) / x[2] ** 5


@register_feynman_eq_class
class FeynmanBonus10(KnownEquation):
    """
    - Equation: Relativistic aberration
    - Raw: (cos(theta2) - v / 2.99792458e8) / (1 - v / 2.99792458e8 * cos(theta2))
    - Num. Vars: 2
    - Vars:
        - x[0]: theta2 (float, positive)
        - x[1]: v (float, positive)
    - Constraints:
        - x[1] / 2.99792458e8 * np.cos(x[0]) != 1
        - (np.cos(x[0]) - x[1] / 2.99792458e8) / (1 - x[1] / 2.99792458e8 * np.cos(x[0])) >= 1
        - (np.cos(x[0]) - x[1] / 2.99792458e8) / (1 - x[1] / 2.99792458e8 * np.cos(x[0])) <= 1
    """
    _eq_name = 'feynman-bonus.10'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                SimpleSampling(0, np.pi, uses_negative=False),
                DefaultSampling(1.0e6, 1.0e8)
            ]

        super().__init__(num_vars=2, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = (sympy.cos(x[0]) - x[1] / SPEED_OF_LIGHT) / (1 - x[1] / SPEED_OF_LIGHT * sympy.cos(x[0]))

    def eq_func(self, x):
        return (np.cos(x[0]) - x[1] / SPEED_OF_LIGHT) / (1 - x[1] / SPEED_OF_LIGHT * np.cos(x[0]))


@register_feynman_eq_class
class FeynmanBonus11(KnownEquation):
    """
    - Equation: N-slit diffraction
    - Raw: I_0 * (sin(alpha / 2) * sin(n * delta / 2) / (alpha / 2 * sin(delta / 2))) ** 2
    - Num. Vars: 4
    - Vars:
        - x[0]: I_0 (float, positive)
        - x[1]: alpha (float, positive)
        - x[2]: n (integer, positive)
        - x[3]: delta (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-bonus.11'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-3, 1.0e-1, uses_negative=False),
                DefaultSampling(1.0e-11, 1.0e-9, uses_negative=False),
                IntegerSampling(1.0, 1.0e2, uses_negative=False), DefaultSampling(1.0e-11, 1.0e-9, uses_negative=False)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * (sympy.sin(x[1] / 2) * sympy.sin(x[2] * x[3] / 2) / (x[1] / 2 * sympy.sin(x[3] / 2))) ** 2

    def eq_func(self, x):
        return x[0] * (np.sin(x[1] / 2) * np.sin(x[2] * x[3] / 2) / (x[1] / 2 * np.sin(x[3] / 2))) ** 2


@register_feynman_eq_class
class FeynmanBonus12(KnownEquation):
    """
    - Equation: 2.11 Jackson
    - Raw: q / (4 * pi * epsilon * y ** 2) * (4 * pi * epsilon * Volt * d - q * d * y ** 3 / (y ** 2 - d ** 2) ** 2)
    - Num. Vars: 5
    - Vars:
        - x[0]: q (float)
        - x[1]: epsilon (float, positive)
        - x[2]: y (float, positive)
        - x[3]: Volt (float)
        - x[4]: d (float, positive)
    - Constraints:
        - x[2] != 0
    """
    _eq_name = 'feynman-bonus.12'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-12, 1.0e-10, uses_negative=False),
                DefaultSampling(1.0e-2, 1.0, uses_negative=False), DefaultSampling(1.0e-1, 1.0e1),
                DefaultSampling(1.0e-2, 1.0, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] / (4 * sympy.pi * x[1] * x[2] ** 2) \
                        * (4 * sympy.pi * x[1] * x[3] * x[4] - x[0] * x[4] * x[2] ** 3 / (x[2] ** 2 - x[4] ** 2) ** 2)

    def eq_func(self, x):
        return x[0] / (4 * np.pi * x[1] * x[2] ** 2) \
               * (4 * np.pi * x[1] * x[3] * x[4] - x[0] * x[4] * x[2] ** 3 / (x[2] ** 2 - x[4] ** 2) ** 2)


@register_feynman_eq_class
class FeynmanBonus13(KnownEquation):
    """
    - Equation: 3.45 Jackson
    - Raw: 1 / (4 * pi * epsilon) * q / sqrt(r ** 2 + d ** 2 - 2 * r * d * cos(alpha))
    - Num. Vars: 5
    - Vars:
        - x[0]: epsilon (float, positive)
        - x[1]: q (float)
        - x[2]: r (float, positive)
        - x[3]: d (float, positive)
        - x[4]: alpha (float, positive)
    - Constraints:
        - x[2] ** 2 + x[3] ** 2 - 2 * x[2] * x[3] * np.cos(x[4]) > 0
    """
    _eq_name = 'feynman-bonus.13'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-12, 1.0e-10, uses_negative=False),
                DefaultSampling(1.0e-3, 1.0e-1), DefaultSampling(1.0e-2, 1.0, uses_negative=False),
                DefaultSampling(1.0e-2, 1.0, uses_negative=False), SimpleSampling(0, np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (4 * sympy.pi * x[0]) * x[1] \
                        / sympy.sqrt(x[2] ** 2 + x[3] ** 2 - 2 * x[2] * x[3] * sympy.cos(x[4]))

    def eq_func(self, x):
        return 1 / (4 * np.pi * ELECTRIC_CONSTANT) * x[1] \
               / np.sqrt(x[2] ** 2 + x[3] ** 2 - 2 * x[2] * x[3] * np.cos(x[4]))


@register_feynman_eq_class
class FeynmanBonus14(KnownEquation):
    """
    - Equation: 4.60' Jackson
    - Raw: Ef * cos(theta) * (-r + d ** 3 / r ** 2 * (alpha - 1) / (alpha + 2))
    - Num. Vars: 5
    - Vars:
        - x[0]: Ef (float)
        - x[1]: theta (float, positive)
        - x[2]: r (float, positive)
        - x[3]: d (float, positive)
        - x[4]: alpha (float, positive)
    - Constraints:
        - x[2] != 0
        - x[4] != -2
    """
    _eq_name = 'feynman-bonus.14'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e1, 1.0e3), SimpleSampling(0, np.pi, uses_negative=False),
                DefaultSampling(1.0e-2, 1.0, uses_negative=False), DefaultSampling(1.0e-2, 1.0, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1, uses_negative=False)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = x[0] * sympy.cos(x[1]) * (-x[2] + x[3] ** 3 / x[2] ** 2 * (x[4] - 1) / (x[4] + 2))

    def eq_func(self, x):
        return x[0] * np.cos(x[1]) * (-x[2] + x[3] ** 3 / x[2] ** 2 * (x[4] - 1) / (x[4] + 2))


@register_feynman_eq_class
class FeynmanBonus15(KnownEquation):
    """
    - Equation: 11.38 Jackson
    - Raw: sqrt(1 - v ** 2 / 2.99792458e8 ** 2) * omega / (1 + v / 2.99792458e8 * cos(theta))
    - Num. Vars: 3
    - Vars:
        - x[0]: v (float, positive)
        - x[1]: omega (float, positive)
        - x[2]: theta (float, positive)
    - Constraints:
        - x[0] / 2.99792458e8 * np.cos(x[2]) != -1
        - 2.99792458e8 ** 2 - x[0] ** 2 >= 0
    """
    _eq_name = 'feynman-bonus.15'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e5, 1.0e7, uses_negative=False), DefaultSampling(1.0e9, 1.0e11, uses_negative=False),
                SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt(1 - x[0] ** 2 / SPEED_OF_LIGHT ** 2) * x[1] / (1 + x[0] / SPEED_OF_LIGHT * sympy.cos(x[2]))

    def eq_func(self, x):
        return np.sqrt(1 - x[0] ** 2 / SPEED_OF_LIGHT ** 2) * x[1] / (1 + x[0] / SPEED_OF_LIGHT * np.cos(x[2]))


@register_feynman_eq_class
class FeynmanBonus16(KnownEquation):
    """
    - Equation: 8.56 Goldstein
    - Raw: sqrt((p - q * A_vec) ** 2 * 2.99792458e8 ** 2 + m ** 2 * 2.99792458e8 ** 4) + q * Volt
    - Num. Vars: 5
    - Vars:
        - x[0]: p (float)
        - x[1]: q (float)
        - x[2]: A_vec (float)
        - x[3]: m (float, positive)
        - x[4]: Volt (float)
    - Constraints:
    """
    _eq_name = 'feynman-bonus.16'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-9, 1.0e-7), DefaultSampling(1.0e-11, 1.0e-9),
                DefaultSampling(1.0e1, 1.0e3), DefaultSampling(1.0e-30, 1.0e-28, uses_negative=False),
                DefaultSampling(1.0e-1, 1.0e1)
            ]

        super().__init__(num_vars=5, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = sympy.sqrt((x[0] - x[1] * x[2]) ** 2 * SPEED_OF_LIGHT ** 2 + x[3] ** 2 * SPEED_OF_LIGHT ** 4) \
                        + x[1] * x[4]

    def eq_func(self, x):
        return np.sqrt((x[0] - x[1] * x[2]) ** 2 * SPEED_OF_LIGHT ** 2 + x[3] ** 2 * SPEED_OF_LIGHT ** 4) + x[1] * x[4]


@register_feynman_eq_class
class FeynmanBonus17(KnownEquation):
    """
    - Equation: 12.80' Goldstein
    - Raw: 1 / (2 * m) * (p ** 2 + m ** 2 * omega ** 2 * x ** 2 * (1 + alpha * x / y))
    - Num. Vars: 6
    - Vars:
        - x[0]: m (float, positive)
        - x[1]: p (float)
        - x[2]: omega (float, positive)
        - x[3]: x (float)
        - x[4]: alpha (float)
        - x[5]: y (float, positive)
    - Constraints:
        - x[0] != 0
        - x[5] != 0
    """
    _eq_name = 'feynman-bonus.17'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e-30, 1.0e-28, uses_negative=False), DefaultSampling(1.0e-9, 1.0e-7),
                DefaultSampling(1.0e9, 1.0e11), DefaultSampling(1.0e-11, 1.0e-9),
                DefaultSampling(1.0e-1, 1.0e1), DefaultSampling(1.0e-11, 1.0e-9, uses_negative=False)
            ]

        super().__init__(num_vars=6, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (2 * x[0]) * (x[1] ** 2 + x[0] ** 2 * x[2] ** 2 * x[3] ** 2 * (1 + x[4] * x[3] / x[5]))

    def eq_func(self, x):
        return 1 / (2 * x[0]) * (x[1] ** 2 + x[0] ** 2 * x[2] ** 2 * x[3] ** 2 * (1 + x[4] * x[3] / x[5]))


@register_feynman_eq_class
class FeynmanBonus18(KnownEquation):
    """
    - Equation: 15.2.1 Weinberg
    - Raw: 3 / (8 * pi * 6.67430e-11) * (2.99792458e8 ** 2 * k_f / r ** 2 + H_G ** 2)
    - Num. Vars: 3
    - Vars:
        - x[0]: k_f (float)
        - x[1]: r (float, positive)
        - x[2]: H_G (float)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-bonus.18'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e1, 1.0e3), DefaultSampling(1.0e8, 1.0e10, uses_negative=False),
                DefaultSampling(1.0, 1.0e2)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 3 / (8 * sympy.pi * GRAVITATIONAL_CONSTANT) * (SPEED_OF_LIGHT ** 2 * x[0] / x[1] ** 2 + x[2] ** 2)

    def eq_func(self, x):
        return 3 / (8 * np.pi * GRAVITATIONAL_CONSTANT) * (SPEED_OF_LIGHT ** 2 * x[0] / x[1] ** 2 + x[2] ** 2)


@register_feynman_eq_class
class FeynmanBonus19(KnownEquation):
    """
    - Equation: 15.2.2 Weinberg
    - Raw: -1 / (8 * pi * 6.67430e-11) * (2.99792458e8 ** 4 * k_f / r ** 2 + H_G ** 2 * 2.99792458e8 ** 2 * (1 - 2 * alpha))
    - Num. Vars: 4
    - Vars:
        - x[0]: k_f (float)
        - x[1]: r (float, positive)
        - x[2]: H_G (float)
        - x[3]: alpha (float)
    - Constraints:
        - x[1] != 0
    """
    _eq_name = 'feynman-bonus.19'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e1, 1.0e3), DefaultSampling(1.0e8, 1.0e10, uses_negative=False),
                DefaultSampling(1.0, 1.0e2, uses_negative=False), SimpleSampling(-10, 10)
            ]

        super().__init__(num_vars=4, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = -1 / (8 * sympy.pi * GRAVITATIONAL_CONSTANT) * (SPEED_OF_LIGHT ** 4 * x[0] / x[1] ** 2 + x[2] ** 2 * SPEED_OF_LIGHT ** 2 * (1 - 2 * x[3]))

    def eq_func(self, x):
        return -1 / (8 * np.pi * GRAVITATIONAL_CONSTANT) * (SPEED_OF_LIGHT ** 4 * x[0] / x[1] ** 2 + x[2] ** 2 * SPEED_OF_LIGHT ** 2 * (1 - 2 * x[3]))


@register_feynman_eq_class
class FeynmanBonus20(KnownEquation):
    """
    - Equation: Klein-Nishina (13.132 Schwarz)
    - Raw: 1 / (4 * pi) * 7.2973525693e-3 ** 2 * 6.626e-34 ** 2 / (9.10938356e-31 ** 2 * 2.99792458e8 ** 2) * (omega_0 / omega) ** 2 * (omega_0 / omega + omega / omega_0 - sin(beta) ** 2)
    - Num. Vars: 3
    - Vars:
        - x[0]: omega_0 (float, positive)
        - x[1]: omega (float, positive)
        - x[2]: beta (float, positive)
    - Constraints:
    """
    _eq_name = 'feynman-bonus.20'

    def __init__(self, sampling_objs=None):
        if sampling_objs is None:
            sampling_objs = [
                DefaultSampling(1.0e9, 1.0e11, uses_negative=False),
                DefaultSampling(1.0e9, 1.0e11, uses_negative=False),
                SimpleSampling(0, 2 * np.pi, uses_negative=False)
            ]

        super().__init__(num_vars=3, sampling_objs=sampling_objs)
        x = self.x
        self.sympy_eq = 1 / (4 * sympy.pi) * FINE_STRUCTURE_CONSTANT ** 2 * PLANCK_CONSTANT ** 2 / (ELECTRON_MASS ** 2 * SPEED_OF_LIGHT ** 2) * (x[0] / x[1]) ** 2 * (x[0] / x[1] + x[1] / x[0] - sympy.sin(x[2]) ** 2)

    def eq_func(self, x):
        return 1 / (4 * np.pi) * FINE_STRUCTURE_CONSTANT ** 2 * PLANCK_CONSTANT ** 2 / (ELECTRON_MASS ** 2 * SPEED_OF_LIGHT ** 2) * (x[0] / x[1]) ** 2 * (x[0] / x[1] + x[1] / x[0] - np.sin(x[2]) ** 2)