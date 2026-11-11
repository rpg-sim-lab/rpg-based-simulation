"""Executor.

Invariant: a worker packet never reads the live world.
"""


class ConcurrentExecutionAdapter:
    def execute(self):
        # must stay deterministic across restore
        return 1


def failure_no_op():
    return None
