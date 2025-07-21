from flask_restx import fields, Model # type: ignore

#SET CONFIG
server_settings_model = Model(
    "ServerSettings",
    {
        "address": fields.String(required=True, description="Server IP address"),
        "port": fields.Integer(required=True, description="Server port"),
    }
)

transcription_settings_model = Model(
    "TranscriptionSettings",
    {
        "compute_power": fields.String(required=True, 
            description="Compute power (e.g., 'COMBINED', 'GPU_ONLY', 'CPU_ONLY')"),
        "transcription_mode": fields.String(required=True, 
            description="Transcription mode (e.g., 'HIGH_ACCURACY', 'LOW_LATENCY')"),
        "num_jobs": fields.Integer(required=True, 
            description="Number of concurrent transcription jobs"),
    }
)

config_model = Model(
    "Config",
    {
        "server_settings": fields.Nested(server_settings_model, 
            required=True, description="Server settings"),
        "transcription_settings": fields.Nested(transcription_settings_model,
            required=True, description="Transcription settings"),
    }
)

#ERROR RESPONSE
error_response_model = Model('ErrorResponse', {
    'error': fields.String(required=True)
})

#SUCCESS RESPONSE
success_response_model = Model('SuccessResponse', {
    'message': fields.String(required=True)
})

#GETCONFIGOPTIONS
config_options_model = Model('ConfigOptions', {
    'compute_power': fields.List(fields.String, description="List of compute power options"),
    'transcription_mode': fields.List(fields.String, description="List of transcription mode options")
})

#TRANSCRIBE
transcribe_args_model = Model('TranscribeArgs', {
    'path_to_audio': fields.String(required=True, description="Path of the file to transcribe"),
    'language': fields.String(required=True, description="Language code (e.g., 'it', 'en', 'fr'). Set to None to enable autodetect")
})

transcribe_success_model = Model('TranscribeSuccess', {
    'job_guid': fields.String(required=True, description="Use the guid to check the staus of the job")
})

job_status_model = Model('JobStatus', {
    'guid': fields.String(required=True),
    'status': fields.String(required=True),
    'result': fields.Raw(description="Result dictionary if job is COMPLETED else None")
})

#CANCEL JOB
guid_model = Model('Guid', {
        'guid': fields.String(required=True)
})

#GET JOBS
job_model = Model('Job', {
    'guid': fields.String(required=True, description='Unique identifier for the job'),
    'status': fields.String(required=True, description='Status of the job', example='COMPLETED'),
})

job_list_model = Model('JobList', {
    'items': fields.List(fields.Nested(job_model), description='List of jobs')
})

#GET SERVER STATUS

cpu_model = Model('CPUModel', {
    'usage_percent': fields.Float(description='Percentage of CPU usage')
})

memory_model = Model('MemoryModel', {
    'total_mb': fields.Integer(description='Total memory in MB'),
    'used_mb': fields.Integer(description='Used memory in MB')
})

gpu_model = Model('GPUModel', {
    'device': fields.Integer(description='GPU device ID'),
    'name': fields.String(description='GPU name'),
    'total_memory_mb': fields.Integer(description='Total GPU memory in MB')
})

server_status_model = Model('ServerStatus', {
    'cpu': fields.Nested(cpu_model, description='CPU usage information'),
    'memory': fields.Nested(memory_model, description='Memory usage information'),
    'gpu': fields.List(fields.Nested(gpu_model), description='List of GPU details or "No GPU available" if not present')
})


#GET LOGS

logs_model = Model('Logs', {
    'logs': fields.String(description='Log file content')
})