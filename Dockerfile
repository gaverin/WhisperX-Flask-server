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

RUN mkdir /var/log/stt-server
RUN mkdir /tmp/results
RUN mkdir /sttServer
RUN mkdir /W

COPY ./config.json /tmp/
COPY ./configuration /sttServer/configuration/
COPY ./doc_models /sttServer/doc_models/
COPY ./model /sttServer/model/
COPY ./restart.sh /sttServer/
COPY ./stt_server.py /sttServer/

WORKDIR /sttServer

EXPOSE 5000

CMD ["python3", "stt_server.py"]
