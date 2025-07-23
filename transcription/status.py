from enum import Enum

class Status(Enum):
    """
            QUEUE: initial value, job instance created
            WORKING: start() method has been called on the worker object
            COMPLETED: worker finished successfully his task
            FAILED: some exception raised in the worker run method
            CANCELLED: process has been forcefully terminated by explicit request
    """
    QUEUE = 0
    WORKING = 1 
    COMPLETED = 2
    FAILED = 3
    CANCELLED = 4

    def __str__(self):
        return self.name
    