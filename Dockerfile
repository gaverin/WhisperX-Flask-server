FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

RUN apt-get update -y && \
  apt-get install -y git ffmpeg software-properties-common && \
  apt-get install -y python3.10 python3-pip

RUN pip3 install setuptools-rust
RUN pip3 install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu118
RUN pip3 install ctranslate2==4.4.0
RUN pip3 install git+https://github.com/m-bain/whisperx.git
RUN pip3 install --ignore-installed Flask
RUN pip3 install flask-restx
RUN pip3 install psutil

RUN mkdir /var/log/WhisperX-Flask-server
RUN mkdir /tmp/jobs
RUN mkdir /WhisperX-Flask-server
RUN mkdir /audio

COPY ./config.json /tmp/
COPY ./configuration /WhisperX-Flask-server/configuration/
COPY ./doc_models /WhisperX-Flask-server/api_models/
COPY ./model /WhisperX-Flask-server/transcription/
COPY ./restart.sh /WhisperX-Flask-server/
COPY ./server.py /WhisperX-Flask-server/

WORKDIR /WhisperX-Flask-server

EXPOSE 5000

CMD ["python3", "server.py"]
