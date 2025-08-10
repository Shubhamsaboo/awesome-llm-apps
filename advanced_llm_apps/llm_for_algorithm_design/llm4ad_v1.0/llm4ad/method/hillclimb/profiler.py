# HillCLimb uses the default profilers
from ...tools.profiler import ProfilerBase
from ...tools.profiler import TensorboardProfiler
from ...tools.profiler import WandBProfiler

HillClimbProfiler = ProfilerBase
HillClimbTensorboardProfiler = TensorboardProfiler
HillClimbWandBProfiler = WandBProfiler
