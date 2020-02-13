FROM jrottenberg/ffmpeg:3.2-ubuntu

# ENV variables for language, and for running sibbiling docker containers (very important)
RUN apt-get update && \
    apt update && \
    apt install -y locales curl && \
    rm -rf /var/lib/apt/lists/*  && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
    apt-get update && \
    apt-get install -y --allow-downgrades docker-ce docker-ce-cli containerd.io

ENV LANG=en_US.utf8 LC_ALL=en_US.UTF-8 PATH="/project/project_bin:${PATH}"
# all of project files will be in /project
WORKDIR /project

# must be an absolute path to binary! otherwise it will cause infinite recursion of docker containers
ENTRYPOINT [ "/usr/local/bin/ffmpeg" ]