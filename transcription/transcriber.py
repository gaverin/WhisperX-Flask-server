import torch # type: ignore
from threading import Lock, Thread, Event

from model.status import Status
from model.transcription_job import *
from configuration.transcription_settings import TranscriptionSettings
from configuration.compute_power import ComputePower
from configuration.transcription_mode import TranscriptionMode

class Transcriber:
    """
        Handles transcription jobs lifecycle and result
    """
    def __init__(self, settings: TranscriptionSettings, output_dir):
        #LOAD CONFIG PARAMETERS
        self._compute_power = settings.get_compute_power()
        self._transcription_mode = settings.get_transcription_mode()
        self._max_jobs = settings.get_num_jobs()
        self._output_dir = output_dir

        self.jobs_count = 0
        self.count_lock = Lock()

        self.jobs = []
        self.jobs_lock = Lock()           
        
        #START WATCHDOG
        self.__shutdown_event = Event()
        self.__watchdog = Thread(target=self.__job_watchdog, daemon=True)
        self.__watchdog.start()


    def transcribe(self, path_to_audio, language):         
        args = ()
        #Chek count and eventually increment safely
        self.count_lock.acquire()
        if self.jobs_count < self._max_jobs:
            #Selct the correct arguments
            if self._transcription_mode == TranscriptionMode.HIGH_ACCURACY and self._compute_power == ComputePower.CPU_ONLY:
                model_size = "large-v2"
                device = "cpu"
                device_index = 0
                compute_type = "int8"
                threads = 4
                batch_size = 4
                args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
            
            elif self._transcription_mode == TranscriptionMode.LOW_LATENCY and self._compute_power == ComputePower.CPU_ONLY:
                model_size = "medium"
                device = "cpu"
                device_index = 0
                compute_type = "float16"
                threads = 4
                batch_size = 4
                args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
            
            elif self._transcription_mode == TranscriptionMode.HIGH_ACCURACY and self._compute_power == ComputePower.GPU_ONLY:
                model_size = "large-v2"
                device = "cuda"
                device_index = 0
                compute_type = "float16"
                threads = 1
                batch_size = 16
                args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
            
            elif self._transcription_mode == TranscriptionMode.LOW_LATENCY and self._compute_power == ComputePower.GPU_ONLY:
                model_size = "medium"
                device = "cuda"
                device_index = 0
                compute_type = "int8"
                threads = 1
                batch_size = 16
                args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
            
            #Start new job
            job = TranscriptionJob(args, self._output_dir)
            job.start()
            self.jobs_count += 1
            self.count_lock.release()

            self.jobs_lock.acquire()
            self.jobs.append(job)
            self.jobs_lock.release()              
            return job.get_guid()
        else:
            self.count_lock.release()
            return None
                                      
    def get_job_status(self, guid):
        self.jobs_lock.acquire()
        for j in self.jobs:
            if j.get_guid() == guid:      
                status = j.get_status()
                self.jobs_lock.release()
                return status
        self.jobs_lock.release()

        return None

    def cancel_job(self, guid):
        success = False
        self.jobs_lock.acquire()
        for j in self._cpu_jobs:
            if j.get_guid() == guid:      
                success = j.cancel_job()
                self.jobs_lock.release()
                return success

        return success

    def get_jobs(self):
        return self.jobs
    
    def shutdown(self):
        self.__shutdown_event.set()  # Signal the thread to stop
        self.__watchdog.join()  # Wait for the thread to finish
    
    
    def __job_watchdog(self):        
        while not self.__shutdown_event.is_set():
            self.count_lock.acquire()
            if self.job_count == 0:   
                self.count_lock.release()
            else:
                for j in self.jobs:
                    status = j.get_status()
                    if status == Status.CANCELLED or status == Status.FAILED or status == Status.COMPLETED:
                        self.jobs_count -= 1
                        self.jobs_lock.acquire()
                        self.jobs.remove(j)
                        self.jobs_lock.release()
                self.count_lock.release()