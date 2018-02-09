# Toil Container

[![pypi](https://img.shields.io/pypi/v/toil_container.svg)](https://pypi.python.org/pypi/toil_container)
[![build](https://img.shields.io/travis/leukgen/toil_container.svg)](https://travis-ci.org/leukgen/toil_container)
[![docs](https://readthedocs.org/projects/toil-container/badge/?version=latest)](https://toil-container.readthedocs.io/en/latest/?badge=latest)
[![updates](https://pyup.io/repos/github/leukgen/toil_container/shield.svg)](https://pyup.io/repos/github/leukgen/toil_container/)


A base python package to create Toil pipelines, using containerized jobs.


# Contents

- [Contents](#contents)
- [Usage](#usage)
- [Installation](#installation)
- [Docker](#docker)
- [Singularity](#singularity)
- [Credits](#credits)


## Usage

Example...


## Installation

Example...

    pip install --editable .


## Docker

Local directories can be mounted in the container using the `--volume` flag. (please note it doesn't need to be `/shared_fs`, it could be `/ifs`).

    # build the image
    docker build --tag toil_container-image .

    # run the container

    toil_container
        [toil options]
        [toil_container options]
        --docker toil_container-image
        --shared-fs /shared_fs
        jobstore


## Singularity

Once created the docker image, run `singularityware/docker2singularity` to create the singularity image. If you are running in a shared file system (e.g. `/shared_fs`), you can mount this directory in the container by using the `-m` flag (multiple `-m` are allowed):

    # build the image
    docker build --tag toil_container-image .

    # this command must be run in a local machine with docker❗️
    docker run \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v `pwd`:/output \
        --privileged -t --rm \
        singularityware/docker2singularity \
            -m '/shared_fs /shared_fs' \
            toil_container-image

The previous command will create a singularity image named with `$creation_date` and `$container_id` variables. These will be unique to each run of `singularityware/docker2singularity`.

    # set the path to the singularity image
    SIGULARITY_IMAGE_PATH=`pwd`/toil_container-image-$creation_date-$container_id.img

    # run the container

    toil_container
        [toil-options]
        [toil_container options]
        --singularity toil_container-image
        --shared-fs /shared_fs
        jobstore


## Credits

This package was created with [Cookiecutter] and the
[audreyr/cookiecutter-pypackage] project template.

  [Cookiecutter]: https://github.com/audreyr/cookiecutter
  [audreyr/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
