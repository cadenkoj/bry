FROM ubuntu:22.04

RUN apt-get update && apt-get install -y locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get update && apt-get install -y python3.11

WORKDIR /app

COPY requirements.txt /app/

RUN py -3 -m pip install -r requirements.txt

CMD ["python3", "main.py"]
