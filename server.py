from flask import Flask, request, jsonify # type: ignore
from flask_restx import Api, Resource # type: ignore

import json
import os
import multiprocessing as mp
import psutil # type: ignore
import torch # type: ignore
import subprocess
import sys

from configuration.config import Config
from transcription.transcriber import Transcriber
from transcription.enums import Status
from transcription.logger import Logger
from api_models.models import *

# FLASK APP AND RESTX API
app = Flask(__name__)
api = Api(app, version="1.0", title="Speech-to-Text Server API", description="API for managing transcription jobs", doc="/api")

# MAIN
def main():
    # LOGGER
    LOG_DIR_PATH = "/var/log/WhisperX-Flask-server"
    logger = Logger(LOG_DIR_PATH)
    logger.log(f"Server started")

    # LOAD CONFIGURATION 
    CONFIG_FILE_PATH = "/tmp/config.json" 
    config = Config(CONFIG_FILE_PATH)
    logger.log(f"Configuration saved in {CONFIG_FILE_PATH}")

    # TRANSCRIBER
    OUTPUT_DIR = "/tmp/jobs" 
    logger.log(f"Transcriptions saved in {OUTPUT_DIR}")
    transcriber = Transcriber(config.get_transcription_settings(), OUTPUT_DIR)
    
    # PID FILE USED IN RESTART
    PID_FILE = "/tmp/WhisperX-Flask-server.pid"
    with open(PID_FILE, 'w') as pid_f:
        pid_f.write(str(os.getpid()))
    logger.log(f"Pid saved in {PID_FILE}")

    # ADD API MODELS FOR RESPONSE AND REQUEST
    api.add_model('Config', config_model)
    api.add_model('ServerSettings', server_settings_model)
    api.add_model('TranscriptionSettings', transcription_settings_model)
    api.add_model('ErrorResponse', error_response_model)
    api.add_model('SuccessResponse', success_response_model)
    api.add_model('ConfigOptions', config_options_model)
    api.add_model('TranscribeArgs', transcribe_args_model)
    api.add_model('TranscribeSuccess', transcribe_success_model)
    api.add_model('JobStatus', job_status_model)
    api.add_model('Guid', guid_model)
    api.add_model('Job', job_model)
    api.add_model('JobList', job_list_model)
    api.add_model('CPUModel', cpu_model)
    api.add_model('MemoryModel', memory_model)
    api.add_model('GPUModel', gpu_model)
    api.add_model('ServerStatus', server_status_model)
    api.add_model('Logs', logs_model)

    # API ROUTES
    @api.route('/setConfig', methods=['POST'])
    class SetConfig(Resource):
        @api.expect(config_model)
        @api.response(200, 'Success', success_response_model)
        @api.response(400, 'Error', error_response_model)
        def post(self):
            """Set configuration"""
            config_dict = request.get_json()
            if Config.validate(config_dict):
                with open(CONFIG_FILE_PATH, "w") as config_file:
                    json.dump(config_dict, config_file)
                logger.log("SetConfig: configuration updated")           
                return {"message": "Configuration received successfully, restart to apply changes"}, 200
            else:
                logger.log("SetConfig: invalid configuration received")
                return {"error": "Invalid configuration"}, 400


    @api.route('/getConfig', methods=['GET'])
    class GetConfig(Resource):
        @api.response(200, 'Config', config_model)
        def get(self):
            """Get current server configuration"""
            return config.get_config(), 200
        

    @api.route('/getConfigOptions', methods=['GET'])
    class GetConfigOptions(Resource):
        @api.response(200, 'ConfigOptions', config_options_model)
        def get():
            """Get options for configuration parameters"""
            return config.get_config_options(), 200


    @api.route('/transcribe', methods=['POST'])
    class Transcribe(Resource):
        @api.expect(transcribe_args_model)
        @api.response(400, 'Error', error_response_model)
        @api.response(200, 'Success', transcribe_success_model)
        def post(self):
            """Start a transcription job"""
            args = request.get_json()
            try:
                path_to_audio = args["path_to_audio"]
                language = args["language"]
            except:
                logger.log("Transcribe: invalid arguments received")
                return {"error": "Invalid arguments"}, 400
            
            guid = transcriber.transcribe(path_to_audio, language)
            if guid is None:
                logger.log("Transcribe: transcription job not started")
                return {"error": f"{config.get_transcription_settings().get_num_jobs()} concurrent transcriptions allowed. Change the configuration"}, 400
            else:
                logger.log(f"Transcribe: job {guid} started")
                return {"job_guid": f"{guid}"}, 200
            

    @api.route('/getJobStatus', methods=['GET'])
    class GetJobStatus(Resource):
        @api.param('guid', 'job guid')
        @api.response(400, 'Error', error_response_model)
        @api.response(200, 'Success', job_status_model)
        def get(self):
            """Get the status of a job"""
            guid = request.args.get('guid')
            if not guid:
                return {"error": "GUID is required"}, 400 
            status = transcriber.get_job_status(guid)
            if status is Status.COMPLETED:
                result_file_path = os.path.join(OUTPUT_DIR, f"{guid}.json")
                with open(result_file_path, "r") as result_file:
                    result = json.load(result_file)
                    return {"guid": guid, "status": str(status), "result": result}, 200
            elif status is not None:
                return {"guid": guid, "status": str(status), "result": None}, 200
            else:
                return {"error": "job doesn't exist"}, 400


    @api.route('/cancelJob', methods=['POST'])
    class CancelJob(Resource):
        @api.expect(guid_model)
        @api.response(400, 'Error', error_response_model)
        @api.response(200, 'Success', success_response_model)
        def post(self):
            """Cancel a job"""
            body = request.get_json()
            try:
                guid = body["guid"]
            except:
                logger.log("CancelJob: no guid specified")
                return {"error": "Invalid arguments"}, 400
            success = transcriber.cancel_job(guid)    
            if success:
                logger.log(f"CancelJob: job {guid} cancelled")
                return {"message": f"job with guid {guid} cancelled correctly"}, 200
            else:
                return {"error": "either the job is not running or the guid is invalid. Check the job status"}, 400 


    @api.route('/getJobs', methods=['GET'])
    class GetJobs(Resource):
        @api.response(200, 'Success', job_list_model)
        def get(self):
            """Get all the jobs and their status"""
            job_list = transcriber.get_jobs()

    @api.route('/restart')
    class Restart(Resource):
        @api.response(200, 'Success', success_response_model)
        def post(self):
            """Restart the server"""
            logger.log("Restart: restarting the server")
            subprocess.run("./restart.sh")
            return {"message": "Server is restarting..."}, 200


    @api.route('/getServerStatus')
    class GetServerStatus(Resource):
        @api.response(200, 'ServerStatus', server_status_model)
        def get(self):
            """Get server system status"""
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            gpu_info = []
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    gpu = torch.cuda.get_device_properties(i)
                    gpu_info.append({"device": i, "name": gpu.name, "total_memory_mb": gpu.total_memory // (1024 ** 2)})

            return {
                "cpu": {"usage_percent": cpu_percent},
                "memory": {"total_mb": memory.total // (1024 ** 2), "used_mb": memory.used // (1024 ** 2)},
                "gpu": gpu_info if gpu_info else "No GPU available"
            }, 200


    @api.route('/getLogs')
    class GetLogs(Resource):
        @api.param('year', 'year')
        @api.param('month', 'month number')
        @api.response(400, 'Error', error_response_model)
        @api.response(200, 'Logs', logs_model)
        def get(self):
            """Get logs for the specified month"""
            year = request.args.get('year')  
            month = request.args.get('month') 
            if not year or not month:
                return {"error": "missing year or month"}, 400
            
            log_file_path = os.path.join(LOG_DIR_PATH, year, month, "app.log")
            if os.path.exists(log_file_path):
                with open(log_file_path, "r") as log_file:
                    logs = log_file.read()
                return {"logs": logs}, 200
            else:
                return {"error": f"log file {log_file_path} not found"}, 400
            

    # START SERVER
    try:
        app.run(host=config.get_server_settings().get_address(), port=config.get_server_settings().get_port())
    except KeyboardInterrupt:
        transcriber.shutdown()

if __name__ == '__main__':
    mp.set_start_method('spawn')
    main()
