FROM continuumio/miniconda3
LABEL maintainer="yvictor"
LABEL maintainer.email="yvictor3141@gmail.com"

COPY . /opt/qc
WORKDIR /opt/qc

RUN pip install pipenv
RUN pipenv sync

CMD pipenv run python -m qc

