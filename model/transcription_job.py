import whisperx # type: ignore
import os
import json
import multiprocessing as mp
from model.job import Job
from model.status import Status

class LimitJobNumberException(Exception):
    pass

class TranscriptionJob(Job):
    """
        Proxy for the transcription job, uses whipserx to transcribe the file 
    """
    def __init__(self, task_args, output_dir):
        super().__init__(task_args, output_dir)
        self._worker = mp.Process(target=self._transcribe, args=(self._result_file_path,)+self._task_args)

    def _transcribe(self, result_file_path, path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size):
        try:
            audio = whisperx.load_audio(path_to_audio)
            model = whisperx.load_model(model_size, device, device_index=device_index, compute_type=compute_type, threads=threads, language=language)
            transcript = model.transcribe(audio, batch_size=batch_size)
            transcript.update({'file':path_to_audio})
            with open(result_file_path, "w") as result_file:
                json_result = json.dumps(transcript)
                json_result = json_result.encode('utf-8').decode('unicode_escape')
                result_file.write(json_result)
        except:
            os._exit(1)
    
    