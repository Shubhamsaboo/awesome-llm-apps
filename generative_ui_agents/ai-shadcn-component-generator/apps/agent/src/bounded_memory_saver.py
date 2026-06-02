"""
Bounded checkpoint storage for LangGraph agents.

The default MemorySaver stores all conversation thread checkpoints in memory
indefinitely. On memory-constrained hosts (e.g. Render's 512MB starter plan),
this causes unbounded growth that eventually triggers an OOM kill.

BoundedMemorySaver caps the number of stored threads and evicts the oldest
(FIFO) when the limit is exceeded. Eviction is tracked with an OrderedDict
rather than sorting keys, so eviction order is correct even when thread IDs
are UUIDs or other non-chronological strings.

NOTE: This class relies on MemorySaver.storage (an internal attribute).
      The langgraph version is pinned in pyproject.toml to guard against
      breaking changes.

NOTE: This class is not thread-safe. It is designed for single-process
      async usage (uvicorn). If deploying with multiple worker threads,
      wrap put() with a threading.Lock.
"""

import logging
from collections import OrderedDict

from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


class BoundedMemorySaver(MemorySaver):
    """MemorySaver that evicts oldest threads when exceeding max_threads."""

    def __init__(self, max_threads: int = 200):
        super().__init__()
        self.max_threads = max_threads
        self._insertion_order: OrderedDict[str, None] = OrderedDict()

    def put(self, config, checkpoint, metadata, new_versions):
        thread_id = config["configurable"]["thread_id"]
        # Move to end if already tracked, otherwise insert
        self._insertion_order[thread_id] = None
        self._insertion_order.move_to_end(thread_id)

        result = super().put(config, checkpoint, metadata, new_versions)

        while len(self.storage) > self.max_threads:
            oldest_thread, _ = self._insertion_order.popitem(last=False)
            if oldest_thread in self.storage:
                logger.info(
                    "BoundedMemorySaver: evicting thread %s (%d threads stored)",
                    oldest_thread,
                    len(self.storage),
                )
                del self.storage[oldest_thread]
        return result
