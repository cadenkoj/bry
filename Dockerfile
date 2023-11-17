FROM ubuntu:22.04

RUN apt-get update && apt-get install -y locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt-get update -qqy --no-install-recommends && apt-get install -qqy --no-install-recommends google-chrome-stable

RUN apt-get install -y curl git python3.11 python3-distutils

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