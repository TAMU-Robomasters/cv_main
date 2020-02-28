FROM jeffhykin/ez_docker:project_bin_1.0.0
# OS: debian, version: buster

# install all the python packages
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# install caffe-cpu
#     why not GPU? because caffe gpu currently only supports nvidia-cuda
#     meaning if your machine doesn't have a CUDA enabled nvidia graphics card
#     and nvidia-docker installed, then it won't work
#     however it is possible the would automatically fallback to caffe-cpu so the idea should still be explored
RUN apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 886DDD89 && \
    add-apt-repository "deb http://ftp2.cn.debian.org/debian sid main contrib non-free" && \
    apt install -y caffe-cpu
