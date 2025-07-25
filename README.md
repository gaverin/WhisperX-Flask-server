# WhisperX-Flask-server
WhisperX-Flask-server is simple speech-to-text containerized microservice based on WhipserX and Flask. It provides a SwaggerUI interface that allows you to easily interact with the APIs and pass the correct arguments.

## Getting started
1. Clone this repository and navigate into it:
    ```
    git clone https://github.com/gaverin/WhisperX-Flask-server.git
    cd WhisperX-Flask-server
    ```
2. Build the Docker container:
    ```
    docker build -t WhisperX-Flask-server .
    ```
3. Run the container and map the host machine directory containing the audio files to the `/audio` directory in the container:
    ```
    docker run --gpus all -p 8080:5000 -v /HOST/AUDIO/DIRECTORY:/audio WhisperX-Flask-server:latest
    ```
4. Open the Swagger UI interface at:  
   `http://<HOST_MACHINE_IP>:8080/api`

## How does it work
Each time the server accepts a transcription request via the `/transcribe` endpoint, a new process is launched. This enables asynchronous processing and allows multiple transcriptions to run concurrently, provided sufficient resources are available.

After the transcription job starts, the server returns a GUID that can be used with the `/getStatus` endpoint to check its progress. Once the Job is completed the trascription is returned with the final status.

> **Note:** Files must be available on the server filesystem. Be sure to mount a local directory to the container.

## Configuration file
Configuration parameters are stored in the `config.json` (copyied in the `/tmp` directory of the container). You can get the transcription settings options using the `/GetConfigOptions` endpoint.

Currently, the WhisperX parameters are abstracted from the client and the service is designed to have two transcription modes:

| Mode            | Model      | Batch Size       | Compute Type               | Threads      |
|-----------------|------------|------------------|----------------------------|--------------|
| `HIGH_ACCURACY` | `large-v2` | 16 (4 on CPU)    | `float16` (`int8` on CPU)  | 1 (4 on CPU) |
| `LOW_LATENCY`   | `medium`   | 16 (4 on CPU)    | `float16` (`int8` on CPU)  | 1 (4 on CPU) |

> **Note:** The parameters  were tuned for an **RTX 4070 Ti** and a **16 core intel i7 CPU**. If you wish to change the behaviour you can check the `transcribe` function in `transcriber.py`

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

## Project Structure
The `server.py` script uses three key modules:

- **configuration**: contains configuration enums and logic for validating the config file;
- **api_models**: defines models used to generate API documentation via Flask-RestX;
- **transcription**: implements the logic to transcribe files asynchronously;

