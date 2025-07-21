from configuration.compute_power import ComputePower
from configuration.transcription_mode import TranscriptionMode

class TranscriptionSettings():

    def __init__(self, compute_power, transcription_mode, num_jobs):
        self._compute_power = ComputePower[compute_power]
        self._transcription_mode = TranscriptionMode[transcription_mode]
        self._num_jobs = num_jobs

    def get_compute_power(self):
        return self._compute_power

    def get_transcription_mode(self):
        return self._transcription_mode

    def get_num_jobs(self):
        return self._num_jobs
    
    def get_options(self):
        compute_power_options = list(ComputePower.__members__.keys())
        transcription_mode_options = list(TranscriptionMode.__members__.keys())
        return {"compute_power": compute_power_options, "transcription_mode": transcription_mode_options}
    
    @staticmethod
    def validate(transcription_settings):
        if not all(key in transcription_settings for key in ['compute_power', 'transcription_mode', 'num_jobs']):
            return False
        if transcription_settings['compute_power'] not in ComputePower.__members__:
            return False
        if transcription_settings['transcription_mode'] not in TranscriptionMode.__members__:
            return False
        if not isinstance(transcription_settings['num_jobs'], int):
            return False
        
        return True
