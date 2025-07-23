# WhisperX-Flask-server
WhisperX-Flask-server is simple speech-to-text containerized microservice based on WhipserX and Flask. It provides a swaggerUI interface that allows you to easily interact with the endpoints and pass the right arguments.

## Getting started


## How does it work
Every time the server accepts a transcription request via the `/transcribe` endpoint, a new process is launched on the server machine so that the request can be processed asynchronously. In this way multiple transcriptions can be performed at the same time if you have enough resources. 

Once a transcription job starts, the server returns a GUID that can be used with the `/getStatus` endpoint to check the progress of that Job. Once the Job is completed the trascription dict is returned with the status.

The files need to be on the server filesystem, therefore you will need to map a local directory to your container.

## Configuration file
The configuration parameters are stored in the `config.json` (copyied in the /tmp directory of the container). You can get the transcription settings options using the `/GetConfigOptions` endpoint.

Currently, the WhisperX parameters are abstracted from the client and the service is designed to have 2 transcription modes:
- `HIGH_ACCURACY`: uses the large-v2 model, batch_size=16 (4 on CPU) and compute_type=float_16 (int 8 on CPU)
- `LOW_LATENCY`: uses the medium model, batch_size=16 (4 on CPU) and compute_type=float_16 (int8 on CPU)

## Endpoints
- `/setConfig`
- `/getConfig`
- `/getConfigOptions`
- `/transcribe`
- `/getJobStatus`
- `/cancelJob`
- `/getJobs`
- `/restart`
- `/getServerStatus`
- `/getLogs`

## Notes
There are 3 modules used by the main script server.py:
- configuration: contains the configuration enums and the logic to validate the configutration file;
- api_models: contains all the models used to generate the API documentation with Flask-RestX
- transcription: contains the logic used to trascribe the files asynchronously

The transcription mode parameters parameters were choosed to maximize the resource usage using an NVIDIA RTX 4070 Ti with 12 GB of VRAM. If you wish to change the behaviour you can check the transcribe function in ``transcriber.py`
