FROM ubuntu:22.04

RUN apt-get update && apt-get install -y locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get install -y curl git python3.11 python3-distutils google-chrome-stable

RUN CHROMEDRIVER_VERSION="114.0.5735.90" && \
    curl -O https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/local/bin/ && \
    rm chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 -

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

RUN useradd -m myuser
USER myuser

CMD ["python3.11", "main.py"]