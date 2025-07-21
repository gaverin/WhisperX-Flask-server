class TranscriptionMode(Enum):
    """
        LOW_LATENCY: Uses medium model 
        HIGH_ACCURACY: Uses large model
    """
    LOW_LATENCY = 0
    HIGH_ACCURACY = 1

    def __str__(self):
        return self.name