class ComputePower(Enum):
    """
        CPU_ONLY: Use only the CPU for computation.
        GPU_ONLY: Use CPU and GPU for computation.
        COMBINED: Use CPU and GPU power
    """
    CPU_ONLY = 0
    GPU_ONLY = 1
    COMBINED = 2

    def __str__(self):
        return self.name