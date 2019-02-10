FROM ubuntu:16.04
LABEL maintainer="yvictor"
LABEL maintainer.email="yvictor3141@gmail.com"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y locales && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.UTF-8

ENV PYENV_ROOT="/.pyenv" \
PATH="/.pyenv/bin:/.pyenv/shims:$PATH"
ENV PIPENV_RUN_SYSTEM=1 \
PIPENV_IGNORE_VIRTUALENVS=0

# gcc g++ optional
RUN apt update && apt install -y openssl make git wget bzip2 ca-certificates curl && \
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash && \
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc && \
    pyenv install miniconda3-latest &&  pyenv global miniconda3-latest &&\
    pyenv rehash && conda install ujson -y

COPY . /opt/qc
WORKDIR /opt/qc

#RUN ["/bin/bash", "-c", "eval \"$(pyenv init -)\" && eval \"$(pyenv virtualenv-init -)\" && pip install pipenv && pipenv install --dev && pipenv sync"]
    #"source ~/.bashrc &&",
    #"pipenv install --dev && pipenv sync"]
#RUN $PYENV_ROOT/versions/miniconda3-latest/bin/python -m pip install pipenv && \
#    $PYENV_ROOT/versions/miniconda3-latest/bin/python -m pipenv install --dev
RUN pip install pipenv && pipenv install --system --dev
 
CMD python -m qc
