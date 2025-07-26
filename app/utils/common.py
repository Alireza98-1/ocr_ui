import logging
import os
from typing import Callable

import psutil 

# It's good practice to have a logger in utility files as well.
logger = logging.getLogger(__name__)

def batchify(iterable: list, preprocess: Callable, batch_size: int = 1) -> list:
    """Splits an iterable into smaller batches and applies a preprocessing function."""
    l = len(iterable)
    batches = []
    for ndx in range(0, l, batch_size):
        batches.append([preprocess(item) for item in iterable[ndx:min(ndx + batch_size, l)]])
    return batches

def get_current_memory_usage_mb() -> float:
    """Returns the current process's memory usage in MB."""
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    # The 'psutil' name is now defined due to the import above.
    except (ImportError, psutil.Error):
        return 0.0

def log_memory_usage(label: str = ""):
    """Logs a message with the current memory usage."""
    mem_mb = get_current_memory_usage_mb()
    if mem_mb > 0:
        # The 'logger' name is now defined.
        logger.info(f"Memory usage {label}: {mem_mb:.2f} MB")
