import warnings

import numpy as np
import sympy
from sympy import Derivative, Matrix, Symbol, simplify, solve, lambdify
from sympy.utilities.misc import func_name

FLOAT32_MAX = np.finfo(np.float32).max
FLOAT32_MIN = np.finfo(np.float32).min
FLOAT32_TINY = np.finfo(np.float32).tiny


class KnownEquation(object):
    _eq_name = None

    def __init__(self, num_vars, sampling_objs, kwargs_list=None):
        super().__init__()
        if kwargs_list is None:
            kwargs_list = [{'real': True} for _ in range(num_vars)]

        assert len(sampling_objs) == num_vars
        assert len(kwargs_list) == num_vars
        self.sampling_objs = sampling_objs
        self.x = [Symbol(f'x{i}', **kwargs) for i, kwargs in enumerate(kwargs_list)]
        self.sympy_eq = None

    def get_eq_name(self, prefix=None, suffix=None):
        if prefix is None:
            prefix = ''
        if suffix is None:
            suffix = ''
        return prefix + self._eq_name + suffix

    def get_var_count(self):
        return len(self.x)

    def get_op_count(self):
        return self.sympy_eq.count_ops()

    def check_num_vars_consistency(self, debug=False):
        num_vars = self.get_var_count()
        num_vars_used = len(self.sympy_eq.atoms(Symbol))
        consistent = num_vars == num_vars_used
        if debug and not consistent:
            print(f'\tnumber of variables (`{num_vars}`) is not consistent with '
                  f'number of those used in sympy_eq (`{num_vars_used}`)')
        return consistent

    def get_domain_range(self):
        min_value = None
        max_value = None
        for sampling_objs in self.sampling_objs:
            sub_min_value = sampling_objs.min_value
            sub_max_value = sampling_objs.max_value
            if min_value is None:
                min_value = sub_min_value
                max_value = sub_max_value
            elif sub_min_value < min_value:
                min_value = sub_min_value
            elif sub_max_value > max_value:
                max_value = sub_max_value
        return np.abs(np.log10(np.abs(max_value - min_value)))

    def eq_func(self, x):
        raise NotImplementedError()

    def check_if_valid(self, values):
        return ~np.isnan(values) * ~np.isinf(values) * ~np.iscomplex(values) * \
            (FLOAT32_MIN <= values) * (values <= FLOAT32_MAX) * (np.abs(values) >= FLOAT32_TINY)

    def create_dataset(self, sample_size, patience=10):
        warnings.filterwarnings('ignore')
        assert len(self.sampling_objs) > 0, f'There should be at least one variable provided in `{self.sympy_eq}`'
        xs = [sampling_func(sample_size) for sampling_func in self.sampling_objs]
        y = self.eq_func(xs)
        # Check if y contains NaN, Infinity, etc
        valid_sample_flags = self.check_if_valid(y)
        valid_sample_size = sum(valid_sample_flags)
        if valid_sample_size == sample_size:
            return np.array([*xs, y]).T

        valid_xs = [x[valid_sample_flags] for x in xs]
        valid_y = y[valid_sample_flags]
        missed_sample_size = sample_size - valid_sample_size
        for i in range(patience):
            xs = [sampling_func(missed_sample_size * 2) for sampling_func in self.sampling_objs]
            y = self.eq_func(xs)
            valid_sample_flags = self.check_if_valid(y)
            valid_xs = [np.concatenate([xs[i][valid_sample_flags], valid_xs[i]]) for i in range(len(xs))]
            valid_y = np.concatenate([y[valid_sample_flags], valid_y])
            valid_sample_size = len(valid_y)
            if valid_sample_size >= sample_size:
                xs = [x[:sample_size] for x in valid_xs]
                y = valid_y[:sample_size]
                return np.array([*xs, y]).T
        raise TimeoutError(f'number of valid samples (`{len(valid_y)}`) did not reach to '
                           f'{sample_size} within {patience} trials')

    def traverse_tree(self, node, dot, from_idx=None, node_list=None, num_digits=4):
        if node_list is None:
            node_list = list()

        if node.is_number:
            dot.attr('node', shape='box')
            node_label = str(node.evalf(num_digits))
        elif isinstance(node, sympy.Symbol):
            dot.attr('node', shape='doublecircle')
            node_label = str(node)
        else:
            dot.attr('node', shape='ellipse')
            node_label = func_name(node)

        current_idx = len(node_list)
        dot.node(str(current_idx), label=node_label)
        node_list.append(current_idx)
        if from_idx is not None:
            dot.edge(str(from_idx), str(current_idx))

        for child_node in node.args:
            self.traverse_tree(child_node, dot, current_idx, node_list, num_digits)

    def find_stationary_points(self, excludes_saddle_points=False):
        if self.sympy_eq is None:
            raise ValueError('`sympy_eq` is None and should be initialized with sympy object')

        # 1st-order partial derivative
        f_primes = [Derivative(self.sympy_eq, var).doit() for var in self.x]

        # Find stationary points
        try:
            stationary_points = solve(f_primes, self.x)
            stationary_points = [sp for sp in map(lambda sp: simplify(sp), stationary_points)
                                 if isinstance(sp, sympy.core.containers.Tuple) and all([s.is_real for s in sp])]
            if len(stationary_points) == 0 or not excludes_saddle_points:
                return stationary_points
        except Exception as e:
            print(f'====={e}=====')
            return []

        # 2nd-order partial derivative
        f_prime_mat = [[Derivative(f_prime, var).doit() for var in self.x] for f_prime in f_primes]

        # Hesse matrix
        hesse_mat = Matrix(f_prime_mat)
        det_hessian = hesse_mat.det()

        # Find saddle points
        saddle_point_list = list()
        diff_stationary_point_list = list()
        for sp in stationary_points:
            pairs = [(var, sp_value) for var, sp_value in zip(self.x, sp)]
            sign_det_hessian = det_hessian.subs(pairs).evalf()
            if sign_det_hessian < 0:
                saddle_point_list.append(sp)
            else:
                diff_stationary_point_list.append(sp)
        return diff_stationary_point_list

    @classmethod
    def from_sympy_eq(cls, sympy_eq, sampling_objs, reindexes=True):
        warnings.filterwarnings('ignore')
        variables = tuple(sorted(sympy_eq.free_symbols, key=lambda x: int(x.name[1:])))
        if reindexes:
            new_variables = tuple([Symbol(f'x{i}') for i in range(len(variables))])
            for old_variable, new_variable in zip(variables, new_variables):
                sympy_eq = sympy_eq.subs(old_variable, new_variable)
            variables = new_variables

        assert len(sampling_objs) == len(variables)
        ds = cls(len(variables), sampling_objs)
        ds.sympy_eq = sympy_eq
        eq_func = lambdify(variables, sympy_eq, modules='numpy')
        ds.eq_func = lambda x: eq_func(*x).T
        return ds