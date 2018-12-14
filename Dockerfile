FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        build-essential \
        python3.6 \
        python3.6-dev \
        python3-pip \
        python-setuptools \
        cmake \
        wget \
        curl \
        libsm6 \
        libxext6 \ 
        libxrender-dev

COPY requirements.txt /tmp

WORKDIR /tmp

RUN curl https://bootstrap.pypa.io/get-pip.py | python3.6
RUN wget --timestamping http://content.sniklaus.com/github/pytorch-hed/network-bsds500.pytorch
RUN python3.6 -m pip install -r requirements.txt

COPY . /pytorch-hed

WORKDIR /pytorch-hed

EXPOSE 50051

RUN python3.6 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. Service/edgedetect.proto

CMD ["python", "Service/server.py"]