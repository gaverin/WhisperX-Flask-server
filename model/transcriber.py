import torch # type: ignore
from threading import Lock, Thread, Event

from model.status import Status
from model.transcription_job import *
from configuration.transcription_settings import TranscriptionSettings
from configuration.compute_power import ComputePower
from configuration.transcription_mode import TranscriptionMode

#TO DO AL POSTO DEL DICTIONARY
class CudaDevice:
    pass

class Transcriber:
    """
        Handles transcription jobs lifecycle and result
    """
    def __init__(self, settings: TranscriptionSettings, output_dir):
        #LOAD CONFIG PARAMETERS
        self._compute_power = settings.get_compute_power()
        self._transcription_mode = settings.get_transcription_mode()
        self._total_max_jobs = settings.get_num_jobs()
        self._output_dir = output_dir

        #GLOBAL COUNTERS AND LIMITS
        self._cpu_jobs_count = 0
        self._cpu_max_jobs = 0
        self._cpu_count_lock = Lock()

        self._cuda_devices = []

        #JOBS
        self._cpu_jobs = []
        self._cpu_jobs_lock = Lock()
        
        #COMPLETED_JOBS
        self._history = []
        self._history_lock = Lock()

        #FIND MAX JOB NUMBER FOR EACH DEVICE
        if self._compute_power == ComputePower.CPU_ONLY:
            self._cpu_max_jobs = total_max_jobs
        else:
            jobs_on_cuda = 0
            if self._compute_power == ComputePower.GPU_ONLY:
                self._cpu_max_jobs = 0
                jobs_on_cuda = total_max_jobs
            elif self._compute_power == ComputePower.COMBINED:
                if total_max_jobs == 1:
                    #GPU device has priority
                    self._cpu_max_jobs = 0
                    jobs_on_cuda = 1
                else:
                    self._cpu_max_jobs = 1
                    jobs_on_cuda = total_max_jobs-1
            #Find all available cuda devices and the one with the biggest VRAM size in case load can't be split uneavenly
            device_count = torch.cuda.device_count()
            for i in range(device_count): 
                total_memory = int(torch.cuda.get_device_properties(i).total_memory / (1024 ** 2))
                cuda_device = { "index" : i, 
                            "total_memory" : total_memory, 
                            "max_jobs" : 0,
                            "job_count": 0,
                            "count_lock": Lock(),
                            "jobs" : [],
                            "jobs_lock" : Lock()
                        }
                self._cuda_devices.append(cuda_device)
            #Split the jobs between the devices
            most_vram_device = max(self._cuda_devices, key=lambda x: x["total_memory"])
            for cuda_device in self._cuda_devices:
                if cuda_device["index"] == most_vram_device["index"]: 
                    cuda_device["max_jobs"] = (jobs_on_cuda // device_count) + (jobs_on_cuda % device_count)
                else:
                    cuda_device["max_jobs"] = (jobs_on_cuda // device_count)                
        
        #START WATCHDOG
        self.__shutdown_event = Event()
        self.__watchdog = Thread(target=self.__job_watchdog, daemon=True)
        self.__watchdog.start()


    def transcribe(self, path_to_audio, language):         
        if self._compute_power == ComputePower.CPU_ONLY:
            args = ()
            #Chek count and eventually increment safely
            self._cpu_count_lock.acquire()
            if self._cpu_jobs_count < self._cpu_max_jobs:
                #Arguments
                if self._transcription_mode == TranscriptionMode.HIGH_ACCURACY:
                    model_size = "large-v2"
                    device = "cpu"
                    device_index = 0
                    compute_type = "int8"
                    threads = 4
                    batch_size = 4
                    args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
                else:
                    model_size = "medium"
                    device = "cpu"
                    device_index = 0
                    compute_type = "float16"
                    threads = 4
                    batch_size = 4
                    args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
                #Start new job
                job = TranscriptionJob(args, self._output_dir)
                job.start()
                self._cpu_jobs_count += 1
                self._cpu_count_lock.release()

                self._cpu_jobs_lock.acquire()
                self._cpu_jobs.append(job)
                self._cpu_jobs_lock.release()              
                return job.get_guid()
            else:
                self._cpu_count_lock.release()
                return None
        #Compute_power is set to GPU_ONLY or COMBINED
        else:
            for cuda_device in self._cuda_devices:
                #Arguments
                args = ()
                cuda_device["count_lock"].acquire()
                if cuda_device["job_count"] < cuda_device["max_jobs"]:
                    if self._transcription_mode == TranscriptionMode.HIGH_ACCURACY:
                        model_size = "large-v2"
                        device = "cuda"
                        device_index = cuda_device["index"]
                        compute_type = "float16"
                        threads = 1
                        batch_size = 16
                        args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
                    else:
                        model_size = "medium"
                        device = "cuda"
                        device_index = cuda_device["index"]
                        compute_type = "int8"
                        threads = 1
                        batch_size = 16
                        args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
                    #start new job
                    job = TranscriptionJob(args, self._output_dir)
                    job.start()
                    cuda_device["job_count"] += 1
                    cuda_device["count_lock"].release()

                    cuda_device["jobs_lock"].acquire()
                    cuda_device["jobs"].append(job)
                    cuda_device["jobs_lock"].release()
                    #DEBUG PRINT
                    print(job._task_args)
                    print(job.get_status())
                    return job.get_guid()
                else:
                    cuda_device["count_lock"].release()
            #if no GPU has space for the job return None
            if self._compute_power == ComputePower.GPU_ONLY:
                return None
            #if compute_power is set to combined try using cpu before raising exception 
            elif self._compute_power == ComputePower.COMBINED:
                #arguments
                args = ()
                self._cpu_count_lock.acquire()
                if self._cpu_jobs_count < self._cpu_max_jobs:
                    if self._transcription_mode == TranscriptionMode.HIGH_ACCURACY:    
                        model_size = "large-v3"
                        device = "cpu"
                        device_index = 0
                        compute_type = "int8"
                        threads = 4
                        batch_size = 4
                        args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
                    else:
                        model_size = "medium"
                        device = "cpu"
                        device_index = 0
                        compute_type = "int8"
                        threads = 4
                        batch_size = 4
                        args = (path_to_audio, model_size, device, device_index, language, compute_type, threads, batch_size)
                    #start new job
                    job = TranscriptionJob(args, self._output_dir)
                    job.start()
                    self._cpu_jobs_count += 1
                    self._cpu_count_lock.release()

                    self._cpu_jobs_lock.acquire()
                    self._cpu_jobs.append(job)
                    self._cpu_jobs_lock.release()  
                    return job.get_guid()
                else:
                    self._cpu_count_lock.release()
                    return None
                                      

    def get_job_status(self, guid):
        #CHECK RUNNING JOBS
        if self._compute_power == ComputePower.CPU_ONLY:
            #ONLY JOBS ON CPU
            self._cpu_jobs_lock.acquire()
            for j in self._cpu_jobs:
                if j.get_guid() == guid:      
                    status = j.get_status()
                    self._cpu_jobs_lock.release()
                    return status
            self._cpu_jobs_lock.release()
        elif self._compute_power == ComputePower.GPU_ONLY:
            #ONLY JOBS ON GPU
            for d in self._cuda_devices:
                d["jobs_lock"].acquire()
                for j in d["jobs"]:
                    if j.get_guid() == guid:
                        status = j.get_status()
                        d["jobs_lock"].release()
                        return status
                d["jobs_lock"].release()
        else:
            #ALL RUNNING JOBS
            self._cpu_jobs_lock.acquire()
            for j in self._cpu_jobs:
                if j.get_guid() == guid:      
                    status = j.get_status()
                    self._cpu_jobs_lock.release()
                    return status
            self._cpu_jobs_lock.release()

            for d in self._cuda_devices:
                d["jobs_lock"].acquire()
                for j in d["jobs"]:
                    if j.get_guid() == guid:
                        status = j.get_status()
                        d["jobs_lock"].release()
                        return status
                d["jobs_lock"].release()
        
        #CHECK JOBS HISTORY
        self._history_lock.acquire()
        for j in self._history:
            if j.get_guid() == guid:
                status = j.get_status()
                self._history_lock.release()
                return status
        self._history_lock.release()

        return None


    def cancel_job(self, guid):
        success = False
        self._cpu_jobs_lock.acquire()
        for j in self._cpu_jobs:
            if j.get_guid() == guid:      
                success = j.cancel_job()
                self._cpu_jobs_lock.release()
                return success
        self._cpu_jobs_lock.release()

        for d in self._cuda_devices:
            d["jobs_lock"].acquire()
            for j in d["jobs"]:
                if j.get_guid() == guid:
                    success = j.cancel()
                    d["jobs_lock"].release()
                    return success
            d["jobs_lock"].release()
        return success


    def get_jobs(self):
        all_jobs = []
        self._cpu_jobs_lock.acquire()
        for j in self._cpu_jobs:
            all_jobs.append({"guid": j.get_guid(), "staus": j.get_status()})
        self._cpu_jobs_lock.release()

        for d in self._cuda_devices:
            d["jobs_lock"].acquire()
            for j in d["jobs"]:
                all_jobs.append({"guid": j.get_guid(), "staus": j.get_status()})
            d["jobs_lock"].release()
        
        return all_jobs
    

    def shutdown(self):
        self.__shutdown_event.set()  # Signal the thread to stop
        self.__watchdog.join()  # Wait for the thread to finish
    
    
    def __job_watchdog(self):
        
        while not self.__shutdown_event.is_set():
            #CHECK JOBS RUNNING ON CPU
            self._cpu_jobs_lock.acquire()
            if len(self._cpu_jobs) == 0:   
                self._cpu_jobs_lock.release()
            else:
                for j in self._cpu_jobs:
                    status = j.get_status()
                    if status == Status.CANCELLED or status == Status.FAILED or status == Status.COMPLETED:
                        self._cpu_count_lock.acquire()
                        self._cpu_jobs_count -= 1
                        self._cpu_count_lock.release()
                        self._cpu_jobs.remove(j)
                        #MOVE JOB TO HISTORY
                        self._history_lock.acquire()
                        self._history.append(j)
                        self._history_lock.release()
                
                self._cpu_jobs_lock.release()

            #CHECK JOBS RUNNING ON GPU
            for cuda_device in self._cuda_devices:
                cuda_device["jobs_lock"].acquire()
                if len(cuda_device["jobs"]) == 0:
                    cuda_device["jobs_lock"].release()
                else:
                    for j in cuda_device["jobs"]:
                        status = j.get_status()
                        if status == Status.CANCELLED or status == Status.FAILED or status == Status.COMPLETED:
                            cuda_device["count_lock"].acquire()
                            cuda_device["job_count"] -= 1
                            cuda_device["count_lock"].release()
                            cuda_device["jobs"].remove(j)
                            #MOVE JOB TO HISTORY
                            self._history_lock.acquire()
                            self._history.append(j)
                            self._history_lock.release()

                    cuda_device["jobs_lock"].release()