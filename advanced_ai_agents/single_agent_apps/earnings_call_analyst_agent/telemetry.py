from __future__ import annotations

import os
import threading

_lock = threading.Lock()
_initialized = False


def setup_telemetry(workflow_name: str = "earnings_call_analyst") -> None:
    global _initialized
    with _lock:
        if _initialized:
            return
        try:
            from monocle_apptrace import setup_monocle_telemetry
        except ImportError:
            return
        exporters = os.getenv("MONOCLE_EXPORTER", "okahu,file")
        setup_monocle_telemetry(
            workflow_name=workflow_name,
            monocle_exporters_list=exporters,
        )
        _initialized = True
