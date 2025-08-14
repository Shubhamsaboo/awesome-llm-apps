"""
A selection of ordinary differential equations primarily from Steven Strogatz's book "Nonlinear Dynamics and Chaos" with manually chosen parameter values and initial conditions.
Some other famous known systems have been selected from other sources, which are included in the dictionary entries as well.
We selected ODEs primarily based on whether they have actually been suggested as models for real-world phenomena as well as on whether they are 'iconic' ODEs in the sense that they are often used as examples in textbooks and/or have recognizable names.
Whenever there were 'realistic' parameter values suggested, we chose those.
In this benchmark, we typically include only one set of parameter values per equation.
Many of the ODEs in Strogatz' book are analyzed in terms of the different limiting behavior for different parameter settings.
For some systems that exhibit wildely different behavior for different parameter settings, we include multiple sets of parameter values as separate equations (e.g., Lorenz system in chaotic and non-chaotic regime).
For each equation, we include two sets of manually chosen initial conditions.
There are 23 equations with dimension 1, 28 equations with dimension 2, 10 equation with dimension 3, and 2 equations with dimension 4.
This results in a total of 63 equations, 4 of which display chaotic behavior.
"""

equations = [
    {
        'id': 1,
        'eq': '(c_0 - x_0 / c_1) / c_2',
        'dim': 1,
        'consts': [[0.7, 1.2, 2.31]],
        'init': [[10.], [3.54]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_1 > 0, c_2 > 0',
        'eq_description': 'RC-circuit (charging capacitor)',
        'const_description': 'c_0: fixed voltage source, c_1: capacitance, c_2: resistance',
        'var_description': 'x_0: charge',
        'source': 'strogatz p.20'
    },
    {
        'id': 2,
        'eq': 'c_0 * x_0',
        'dim': 1,
        'consts': [[0.23]],
        'init': [[4.78], [0.87]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': '',
        'eq_description': 'Population growth (naive)',
        'const_description': 'c_0: growth rate',
        'var_description': 'x_0: population',
        'source': 'strogatz p.22'
    },
    {
        'id': 4,
        'eq': '1 / (1 + exp(c_0 - x_0 / c_1)) - 0.5',
        'dim': 1,
        'consts': [[0.5, 0.96]],
        'init': [[0.8], [0.02]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_1 > 0',
        'eq_description': 'RC-circuit with non-linear resistor (charging capacitor)',
        'const_description': 'c_0: fixed voltage source, c_1: capacitance',
        'var_description': 'x_0: charge',
        'source': 'strogatz p.38'
    },
    {
        'id': 5,
        'eq': 'c_0 - c_1 * x_0^2',
        'dim': 1,
        'consts': [[9.81, 0.0021175]],
        'init': [[0.5], [73.]],
        'init_constraints': '',
        'const_constraints': 'c_0 > 0, c_1 > 0',
        'eq_description': 'Velocity of a falling object with air resistance',
        'const_description': 'c_0: gravitational acceleration, c_1: overall drag for human: 0.5 * C * rho * A / m, with drag coeff C=0.7, air density rho=1.21, cross-sectional area A=0.25, mass m=50',
        'var_description': 'x_0: velocity',
        'source': 'strogatz p.38'
    },
    {
        'id': 7,
        'eq': 'c_0 * x_0 * log(c_1 * x_0)',
        'dim': 1,
        'consts': [[0.032, 2.29]],
        'init': [[1.73], [9.5]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_0 > 0, c_1 > 0',
        'eq_description': 'Gompertz law for tumor growth',
        'const_description': 'c_0: growth rate, c_1: tumor carrying capacity',
        'var_description': 'x_0: proportional to number of cells (tumor size)',
        'source': 'strogatz p.39'
    },
    {
        'id': 8,
        'eq': 'c_0 * x_0 * (1 - x_0 / c_1) * (x_0 / c_2 - 1)',
        'dim': 1,
        'consts': [[0.14, 130., 4.4]],
        'init': [[6.123], [2.1]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_0 > 0, c_1 > 0, c_2 > 0',
        'eq_description': 'Logistic equation with Allee effect',
        'const_description': 'c_0: growth rate, c_1: carrying capacity, c_2: Allee effect parameter',
        'var_description': 'x_0: population',
        'source': 'strogatz p.39'
    },
    {
        'id': 10,
        'eq': '(1 - x_0) * c_0 * x_0^c_1 - x_0 * (1 - c_0) * (1 - x_0)^c_1',
        'dim': 1,
        'consts': [[0.2, 1.2]],
        'init': [[0.83], [0.34]],
        'init_constraints': '0 < x_0 < 1',
        'const_constraints': '0 <= c_0 <= 1, c_1 > 1',
        'eq_description': 'Refined language death model for two languages',
        'const_description': 'c_0: perceived status of language 1, c_1: adjustable exponent',
        'var_description': 'x_0: proportion of population speaking language 1',
        'source': 'strogatz p.40'
    },
    {
        'id': 13,
        'eq': 'c_0 * sin(x_0) * (c_1 * cos(x_0) - 1)',
        'dim': 1,
        'consts': [[0.0981, 9.7]],
        'init': [[3.1], [2.4]],
        'init_constraints': '',
        'const_constraints': 'c_0 > 0, c_1 > 0',
        'eq_description': 'Overdamped bead on a rotating hoop',
        'const_description': 'c_0: m * g, for m: mass, g: gravitational acceleration, c_1: r * omega^2 / g, for r: radius, omega: angular velocity',
        'var_description': 'x_0: angle',
        'source': 'strogatz p.63'
    },
    {
        'id': 15,
        'eq': 'c_0 * x_0 * (1 - x_0 / c_1) - x_0^2 / (1 + x_0^2)',
        'dim': 1,
        'consts': [[0.4, 95.]],
        'init': [[44.3], [4.5]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_0 > 0, c_1 > 0',
        'eq_description': 'Budworm outbreak with predation (dimensionless)',
        'const_description': 'c_0: growth rate (<0.5 for young forest, 1 for mature), c_1: carrying capacity (~300 for young forest)',
        'var_description': 'x_0: population',
        'source': 'strogatz p.76'
    },
    {
        'id': 16,
        'eq': 'c_0 * x_0 - c_1 * x_0^3 - c_2 * x_0^5',
        'dim': 1,
        'consts': [[0.1, -0.04, 0.001]],
        'init': [[0.94], [1.65]],
        'init_constraints': '',
        'const_constraints': 'c_0 > 0',
        'eq_description': 'Landau equation (typical time scale tau = 1)',
        'const_description': 'c_0: small dimensionless parameter, c_1: constant, c_2: constant; c_1 > 0 for supercritical bifurcation; c_1 < 0 and c_2 > 0 for subcritical bifurcation',
        'var_description': 'x_0: order parameter',
        'source': 'strogatz p.87'
    },
    {
        'id': 18,
        'eq': 'c_0 * x_0 * (1 - x_0 / c_1) - c_2 * x_0 / (c_3 + x_0)',
        'dim': 1,
        'consts': [[0.4, 100., 0.24, 50.]],
        'init': [[21.1], [44.1]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_0 > 0, c_1 > 0, c_2 > 0, c_3 > 0',
        'eq_description': 'Improved logistic equation with harvesting/fishing',
        'const_description': 'c_0: growth rate, c_1: carrying capacity, c_2: harvesting rate, c_3: harvesting onset',
        'var_description': 'x_0: population',
        'source': 'strogatz p.90'
    },
    {
        'id': 19,
        'eq': 'x_0 * (1 - x_0) - c_0 * x_0 / (c_1 + x_0)',
        'dim': 1,
        'consts': [[0.08, 0.8]],
        'init': [[0.13], [0.03]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_0 > 0, c_1 > 0',
        'eq_description': 'Improved logistic equation with harvesting/fishing (dimensionless)',
        'const_description': 'c_0: harvesting rate, c_1: harvesting onset',
        'var_description': 'x_0: population',
        'source': 'strogatz p.90'
    },
    {
        'id': 20,
        'eq': 'c_0 - c_1 * x_0 + x_0^2 / (1 + x_0^2)',
        'dim': 1,
        'consts': [[0.1, 0.55]],
        'init': [[0.002], [0.25]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_0 >= 0, c_1 > 0',
        'eq_description': 'Autocatalytic gene switching (dimensionless)',
        'const_description': 'c_0: basal production rate, c_1: degradation rate',
        'var_description': 'x_0: gene product',
        'source': 'strogatz p.91'
    },
    {
        'id': 21,
        'eq': 'c_0 - c_1 * x_0 - exp(-x_0)',
        'dim': 1,
        'consts': [[1.2, 0.2]],
        'init': [[0.], [0.8]],
        'init_constraints': 'x_0 >= 0',
        'const_constraints': 'c_0 >= 1, c_1 > 0',
        'eq_description': 'Dimensionally reduced SIR infection model for dead people (dimensionless)',
        'const_description': 'c_0: death rate, c_1: unknown parameter group',
        'var_description': 'x_0: dead people',
        'source': 'strogatz p.92'
    },
    {
        'id': 22,
        'eq': 'c_0 + c_1 * x_0^5 / (c_2 + x_0^5) - c_3 * x_0',
        'dim': 1,
        'consts': [[1.4, 0.4, 123., 0.89]],
        'init': [[3.1], [6.3]],
        'init_constraints': 'x_0 > 0',
        'const_constraints': 'c_0 > 0, c_1 > 0, c_2 > 0, c_3 > 0',
        'eq_description': 'Hysteretic activation of a protein expression (positive feedback, basal promoter expression)',
        'const_description': 'c_0: basal transcription rate, c_1: maximum transcription rate, c_2: activation coefficient, c_3: decay rate',
        'var_description': 'x_0: protein concentration',
        'source': 'strogatz p.93'
    },
    {
        'id': 23,
        'eq': 'c_0 - sin(x_0)',
        'dim': 1,
        'consts': [[0.21]],
        'init': [[-2.74], [1.65]],
        'init_constraints': '-pi <= x_0 <= pi',
        'const_constraints': 'c_0 > 0',
        'eq_description': 'Overdamped pendulum with constant driving torque/fireflies/Josephson junction (dimensionless)',
        'const_description': 'c_0: ratio of driving torque to maximum gravitational torque',
        'var_description': 'x_0: angle',
        'source': 'strogatz p.104'
    }
]
