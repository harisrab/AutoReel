FROM python:3.8

RUN mkdir -p /reels_generator
WORKDIR /reels_generator

ADD ./requirements.txt ./
ADD ./data/ ./
ADD ./main.py ./
ADD ./helpers.py ./
ADD ./WhisperSileroVAD.py ./
ADD ./README.md ./
ADD ./output ./
ADD ./missing_data ./

ARG APT_FILE=/etc/apt/sources.list

# # change apt repo source
# RUN mv $APT_FILE $APT_FILE.bak && \
#   touch $APT_FILE && \
#   echo  "deb http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb-src http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb-src http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb-src http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb-src http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse" >> $APT_FILE && \
#   echo "deb-src http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse" >> $APT_FILE

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32

RUN apt-get update && apt-get install -y python-dev pkg-config

# add a new ffmpeg source, the builtin is too old
# RUN apt-get update && apt-get install -y software-properties-common &&\
#     add-apt-repository -y ppa:jonathonf/ffmpeg-4

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev 

RUN pip3 install -r requirements.txt

RUN pip install av
RUN pip install -U openai-whisper


CMD ["python3", "main.py"]