FROM       python:3.7
MAINTAINER Steven Tong "https://github.com/sntong"

RUN apt-get update

RUN apt-get install -y sudo curl 
RUN apt-get install -y bash bash-doc bash-completion
RUN apt-get install -y util-linux pciutils usbutils coreutils binutils findutils grep
RUN apt-get install -y build-essential libssl-dev
RUN apt-get install -y git
# Install language pack
RUN apt-get install -y locales
RUN locale-gen zh_TW zh_TW.UTF-8 zh_CN.UTF-8 en_US en_US.UTF-8 C.UTF-8

RUN dpkg-reconfigure locales
# Set the lang, you can also specify it as as environment variable through docker-compose.yml
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

RUN pip install pillow==6.0.0
RUN pip install baidu-aip

RUN mkdir -p /root/xxvideo
RUN chmod 777 /root/xxvideo
RUN cd /root && git clone --depth=1 https://github.com/snhome/javsdt.git

SHELL ["/bin/bash", "-c"]

CMD tail -f /dev/null