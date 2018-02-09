# Use base image
FROM  python:2.7-jessie

# File Author / Maintainer
LABEL Mantainer Juan S. Medina, Juan E. Arango <medinaj@mskcc.org, arangooj@mskcc.org>

# Define directories
ENV OUTPUT_DIR /data
ENV WORK_DIR /code
ENV OPT_DIR /opt

# For cookiecutter-testing
ENV PROJECT toil_container

# Mount the output volume as persistant
VOLUME ${OUTPUT_DIR}

RUN \
    # Install Packages Dependencies
    apt-get update -yqq && \
    apt-get install -yqq \
    curl \
    git \
    locales \
    python-pip \
    wget && \
    apt-get clean && \
    \
    ## Configure default locale, see https://github.com/rocker-org/rocker/issues/19
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen en_US.utf8 && \
    /usr/sbin/update-locale LANG=en_US.UTF-8

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

# Install toil_container
COPY . ${WORK_DIR}
WORKDIR ${WORK_DIR}
RUN pip install --editable .

# Run command
ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
