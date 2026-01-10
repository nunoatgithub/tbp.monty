import pytest

"""Pytest configuration for shared memory cleanup with xdist support."""
from shm_rpc_bridge.transport.transport_chooser import SharedMemoryTransport

def pytest_configure(config):
    if not hasattr(config, "workerinput"):
        # Runs only on master, before workers start
        SharedMemoryTransport.delete_resources()

def pytest_sessionfinish(session):
    if not hasattr(session.config, "workerinput"):
        # Runs only on master, after workers return
        SharedMemoryTransport.delete_resources()

@pytest.fixture(autouse=True)
def flush_logs_after_test(request):
    """Flush logs after each test to ensure spawned process logs are captured."""
    yield
    import logging
    from shm_rpc_bridge import get_logger
    import sys

    # Flush all handlers to ensure logs from spawned processes are written
    for handler in logging.getLogger().handlers:
        handler.flush()

    logger = get_logger()
    for handler in logger.handlers:
        handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()