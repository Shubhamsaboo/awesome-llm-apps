# RandSample uses the default profilers
from ...tools.profiler import ProfilerBase
from ...tools.profiler import TensorboardProfiler
from ...tools.profiler import WandBProfiler

RandSampleProfiler = ProfilerBase
RandSampleTensorboardProfiler = TensorboardProfiler
RandSampleWandBProfiler = WandBProfiler
