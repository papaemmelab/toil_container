FROM python:2.7-jessie

LABEL maintainers="\
    Juan S. Medina <https://github.com/jsmedmar>, \
    Juan E. Arango <https://github.com/juanesarango>"

# define directories
ENV OUTPUT_DIR /data
ENV WORK_DIR /code

# for cookiecutter-testing
ENV PROJECT toil_container

# mount the output volume as persistant
VOLUME ${OUTPUT_DIR}

RUN \
    # install Packages Dependencies
    apt-get update -yqq && \
    apt-get install -yqq \
    curl \
    git \
    locales \
    python-pip \
    wget && \
    apt-get clean && \
    \
    # configure locale, see https://github.com/rocker-org/rocker/issues/19
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen en_US.utf8 && \
    /usr/sbin/update-locale LANG=en_US.UTF-8

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

# install toil_container
COPY . ${WORK_DIR}
WORKDIR ${WORK_DIR}
RUN pip install --editable .

