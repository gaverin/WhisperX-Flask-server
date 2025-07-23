import whisperx # type: ignore
import os
import json
import uuid
import os
import time
from datetime import datetime
import multiprocessing as mp
from model.status import Status

class TranscriptionJob:
    """
        Proxy for the transcription job, uses whipserx to transcribe the file 
    """
    def __init__(self, task_args, output_dir):
        self._guid = uuid.uuid4()
        self._status = Status.QUEUE
        self._task_args = task_args
        self._output_dir = output_dir
        self._result_file_path = os.path.join(output_dir, str(self._guid) + ".json")
        self._start_time = None
        self._end_time = None
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
    
    
    def get_guid(self) -> str:
        return str(self._guid)
    

    def get_status(self) -> Status:
        if self._status == Status.CANCELLED:
            return self._status
        
        if self._start_time is not None:
            if self._worker.exitcode == None:
                self._status = Status.WORKING
            
            elif self._worker.exitcode == 0:
                self._end_time = datetime.fromtimestamp(time.time())
                self._status = Status.COMPLETED

            else:
                self._end_time = datetime.fromtimestamp(time.time())
                self._status = Status.FAILED
        
        #update timestamp
        return self._status

    
    def cancel(self) -> bool:
        if self._status == Status.COMPLETED or self._status == Status.FAILED:
            return False
        
        elif self._status == Status.QUEUE:
            self._end_time = datetime.fromtimestamp(time.time())
            self._status = Status.CANCELLED
        
        else:
            self._worker.terminate()
            self._end_time = datetime.fromtimestamp(time.time())
            self._status = Status.CANCELLED
            return True
        
    
    def start(self):
        self._worker.start()
        self._start_time = datetime.fromtimestamp(time.time())

    
    def __str__(self):
        if self._start_time is None:
            return str({"GUID": str(self._guid), "job_status": str(self._status), "start_time" : None, "end_time" : None, "args": self._task_args})
        elif self._end_time is None:
            return str({"GUID": str(self._guid), "job_status": str(self._status), "start_time" : self._start_time.strftime("%Y-%m-%d %H:%M:%S"), "end_time" : None, "args": self._task_args})
        else:
            return str({"GUID": str(self._guid), "job_status": str(self._status), "start_time" : self._start_time.strftime("%Y-%m-%d %H:%M:%S"), "end_time" : self._end_time.strftime("%Y-%m-%d %H:%M:%S"), "args": self._task_args})
    
    