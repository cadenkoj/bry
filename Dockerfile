FROM ubuntu:22.04

RUN apt-get install -y git python3.11 python3-distutils

RUN wget python3.11 get-pip.py && \
    rm get-pip.py

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["python3.11", "main.py"]