class ComputePower(Enum):
    """
        CPU_ONLY: Use only the CPU for computation.
        GPU_ONLY: Use only the GPU for computation.
    """
    CPU_ONLY = 0
    GPU_ONLY = 1

    def __str__(self):
        return self.name