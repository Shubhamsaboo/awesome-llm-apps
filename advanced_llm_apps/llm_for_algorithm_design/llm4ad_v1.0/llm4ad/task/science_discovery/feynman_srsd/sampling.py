import numpy as np

def default_sampling(sample_size, min_value=1.0e-1, max_value=1.0e1):
    # x ~ either U(0.1, 10.0) or U(-10.0, -0.1) with 50% chance
    np.random.seed(2025)
    num_positives = sum(np.random.uniform(0.0, 1.0, size=sample_size) > 0.5)
    num_negatives = sample_size - num_positives
    log10_min = np.log10(min_value)
    log10_max = np.log10(max_value)
    pos_samples = 10.0 ** np.random.uniform(log10_min, log10_max, size=num_positives)
    neg_samples = -10.0 ** np.random.uniform(log10_min, log10_max, size=num_negatives)
    all_samples = np.concatenate([pos_samples, neg_samples])
    np.random.shuffle(all_samples)
    return all_samples


def default_positive_sampling(sample_size, min_value=1.0e-1, max_value=1.0e1):
    # x ~ U(0.1, 10.0)
    np.random.seed(2025)
    log10_min = np.log10(min_value)
    log10_max = np.log10(max_value)
    return 10.0 ** np.random.uniform(log10_min, log10_max, size=sample_size)


def default_negative_sampling(sample_size, min_value=1.0e-1, max_value=1.0e1):
    # x ~ U(-10.0, -0.1)
    np.random.seed(2025)
    log10_min = np.log10(abs(min_value))
    log10_max = np.log10(abs(max_value))
    return -10.0 ** np.random.uniform(log10_min, log10_max, size=sample_size)


def simple_sampling(sample_size, min_value=0.0, max_value=1.0):
    # x ~ either U(0.0, 1.0) or U(-1.0, 0.) with 50% chance
    np.random.seed(2025)
    num_positives = sum(np.random.uniform(0.0, 1.0, size=sample_size) > 0.5)
    num_negatives = sample_size - num_positives
    pos_samples = np.random.uniform(min_value, max_value, size=num_positives)
    neg_samples = -np.random.uniform(min_value, max_value, size=num_negatives)
    all_samples = np.concatenate([pos_samples, neg_samples])
    np.random.shuffle(all_samples)
    return all_samples


def simple_positive_sampling(sample_size, min_value=0.0, max_value=1.0):
    # x ~ U(0.0, 1.0)
    np.random.seed(2025)
    return np.random.uniform(min_value, max_value, size=sample_size)



def simple_negative_sampling(sample_size, min_value=0.0, max_value=1.0):
    # x ~ U(-1, 0.0)
    np.random.seed(2025)
    return -np.random.uniform(min_value, max_value, size=sample_size)



def integer_sampling(sample_size, min_value=1, max_value=100):
    # x ~ either U(1, 100) or U(-100, -1) with 50% chance
    np.random.seed(2025)
    num_positives = sum(np.random.uniform(0.0, 1.0, size=sample_size) > 0.5)
    num_negatives = sample_size - num_positives
    pos_samples = np.random.randint(min_value, max_value, size=num_positives)
    neg_samples = -np.random.randint(min_value, max_value, size=num_negatives)
    all_samples = np.concatenate([pos_samples, neg_samples])
    np.random.shuffle(all_samples)
    return all_samples


def integer_positive_sampling(sample_size, min_value=1, max_value=100):
    # x ~ U(1, 100)
    np.random.seed(2025)
    return np.random.randint(min_value, max_value, size=sample_size)



def integer_negative_sampling(sample_size, min_value=1, max_value=100):
    # x ~ U(-100, -1)
    np.random.seed(2025)
    return -np.random.randint(min_value, max_value, size=sample_size)


# @register_sampling_class
class DefaultSampling(object):
    def __init__(self, min_value, max_value, uses_positive=True, uses_negative=True):
        self.min_value = min_value
        self.max_value = max_value
        assert uses_positive or uses_negative
        self.uses_positive = uses_positive
        self.uses_negative = uses_negative

    def __call__(self, sample_size):
        if self.uses_positive and self.uses_negative:
            return default_sampling(sample_size, self.min_value, self.max_value)
        elif self.uses_positive:
            return default_positive_sampling(sample_size, self.min_value, self.max_value)
        elif self.uses_negative:
            return default_negative_sampling(sample_size, self.min_value, self.max_value)
        raise AttributeError(f'Either self.uses_positive ({self.uses_positive}) or '
                             f'self.uses_negative({self.uses_negative}) must be True')


# @register_sampling_class
class SimpleSampling(object):
    def __init__(self, min_value, max_value, uses_positive=True, uses_negative=True):
        self.min_value = min_value
        self.max_value = max_value
        assert uses_positive or uses_negative
        self.uses_positive = uses_positive
        self.uses_negative = uses_negative

    def __call__(self, sample_size):
        if self.uses_positive and self.uses_negative:
            return simple_sampling(sample_size, self.min_value, self.max_value)
        elif self.uses_positive:
            return simple_positive_sampling(sample_size, self.min_value, self.max_value)
        elif self.uses_negative:
            return simple_negative_sampling(sample_size, self.min_value, self.max_value)
        raise AttributeError(f'Either self.uses_positive ({self.uses_positive}) or '
                             f'self.uses_negative({self.uses_negative}) must be True')


# @register_sampling_class
class IntegerSampling(object):
    def __init__(self, min_value, max_value, uses_positive=True, uses_negative=True):
        self.min_value = int(min_value)
        self.max_value = int(max_value)
        assert uses_positive or uses_negative
        self.uses_positive = uses_positive
        self.uses_negative = uses_negative

    def __call__(self, sample_size):
        if self.uses_positive and self.uses_negative:
            return integer_sampling(sample_size, self.min_value, self.max_value)
        elif self.uses_positive:
            return integer_positive_sampling(sample_size, self.min_value, self.max_value)
        elif self.uses_negative:
            return integer_negative_sampling(sample_size, self.min_value, self.max_value)
        raise AttributeError(f'Either self.uses_positive ({self.uses_positive}) or '
                             f'self.uses_negative({self.uses_negative}) must be True')


# def build_sampling_objs(sampling_obj_configs):
#     sampling_obj_list = list()
#     for sampling_obj_config in sampling_obj_configs:
#         sampling_type = sampling_obj_config['type']
#         sampling_kwargs = sampling_obj_config.get('kwargs', dict())
#         sampling_obj = get_sampling_obj(sampling_type, **sampling_kwargs)
#         sampling_obj_list.append(sampling_obj)
#     return sampling_obj_list