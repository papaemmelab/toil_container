# Toil Container

[![pypi badge][pypi_badge]][pypi_base]
[![gitter badge][gitter_badge]][gitter_base]
[![travis badge][travis_badge]][travis_base]
[![pyup badge][pyup_badge]][pyup_base]
[![codecov badge][codecov_badge]][codecov_base]
[![code formatting][black_badge]][black_base]

A python package with container support for [Toil] pipelines.

Check the [example](#usage)! This package was built to support the 🍪 [cookiecutter-toil] repository. Singularity versions that have been tested against:

* Singularity 2.4.2
* Singularity 2.6.1

## Features

- 📦 &nbsp; **Easy Installation**

          pip install toil_container

- 🐳 &nbsp; **Container System Calls**

    `docker_call` and `singularity_call` are functions that run containerized commands with the same calling signature. Be default the `exit code` is returned, however you can get the `stdout` with `check_output=True`. You can also set the `env`, `cwd`, `volumes` and `working_dir` for the container call. `working_dir` is used as the `/tmp` directory inside the container.

    ```python
    from toil_container import docker_call
    from toil_container import singularity_call

    cmd = ["cowsay", "hello world"]
    status = docker_call("docker/whalesay", cmd)
    output = docker_call("docker/whalesay", cmd, check_output=True)

    status = singularity_call("docker://docker/whalesay", cmd)
    output = singularity_call("docker://docker/whalesay", cmd, check_output=True)
    ```

- 🛳 &nbsp; **Container Job Class**

    `ContainerJob` is a [Toil Job Class] with a `call` method that executes commands with either `Docker`, `Singularity` or `Subprocess` depending on image availability. Check out this simple [whalesay example](#usage)! The Job must be constructed with an `options` argument of the type `argparse.Namespace` that may have the following attributes:

    | attribute             | action                  | description             |
    | --------------------- | ----------------------- | ----------------------- |
    | `options.docker`      | use docker              | name or path to image   |
    | `options.singularity` | use singularity         | name or path to image   |
    | `options.workDir`     | set as container `/tmp` | path to work directory  |
    | `options.volumes`     | volumes to be mounted   | list of src, dst tuples |

- 🔌 &nbsp; **Extended LSF functionality**

    By running with `--batchSystem custom_lsf`, it provides 2 features:

    1. Allows to pass its own `runtime (int)` to each job in LSF using `-W`.
    2. Automatic retry of the job by doubling the initial runtime, if the job is killed by `TERM_RUNLIMIT`.

    Additionally, it provides an optimization to cache running jobs status from calling all current jobs (`bjobs`) once, instead of one by one.

    <a id="custom-lsf-support">**NOTE**</a>: The original `toil.Job` class, doesn't provide an option to set `runtime` per job. You could only set a wall runtime globally by adding `-W <runtime>` in `TOIL_LSF_ARGS`. (see:
    [BD2KGenomics/toil#2065]). Please note that our hack, encodes the `runtime` requirements in the job's `unitName`, so your log files will have a longer name. Let us know if you need more custom parameters or if you know of a better solution 😄 .You can set a default runtime in minutes with environment variable `TOIL_CONTAINER_RUNTIME`. Configure `custom_lsf` with the following environment variables:

     `ContainerJob`

    | option                       | description                                        |
    | ---------------------------- | -------------------------------------------------- |
    | TOIL_CONTAINER_RUNTIME       | set a default runtime in minutes                   |
    | TOIL_CONTAINER_RETRY_MEM     | retry memory in integer GB (default "60")          |
    | TOIL_CONTAINER_RETRY_RUNTIME | retry runtime in integer minutes (default "40000") |
    | TOIL_CONTAINER_RUNTIME_FLAG  | bsub runtime flag (default "-W")                   |
    | TOIL_CONTAINER_LSF_PER_CORE  | 'Y' if lsf resources are per core, and not per job |

- 📘 &nbsp; **Container Parser With Short Toil Options**

    `ContainerArgumentParser` adds the `--docker`, `--singularity` and `--volumes` arguments to the options namespace. This parser only prints the required toil arguments when using `--help`. However, the full list of toil rocketry is printed with `--help-toil`. If you don't need the container options but want to use `--help-toil` use `ToilShortArgumentParser`.

         whalesay.py --help-container

             usage: whalesay [-h] [-v] [--help-toil] [TOIL OPTIONAL ARGS] jobStore

              optional arguments:
              -h, --help            show this help message and exit
              --help-toil           show help with toil arguments and exit
              --help-container      show help with container arguments and exit

              container arguments:
              --docker              name/path of the docker image available in daemon
              --singularity         name/path of the singularity image available in deamon
              --volumes             tuples of (local path, absolute container path)

              toil arguments:
              TOIL OPTIONAL ARGS    see --help-toil for a full list of toil parameters
              jobStore              the location of the job store for the workflow [REQUIRED]

## Usage

`whalesay.py` is an example that runs a toil pipeline with the famous [whalesay] docker container. The pipeline can now be executed with either docker, singularity or subprocess.

```python
# whalesay.py
from toil_container import ContainerJob
from toil_container import ContainerArgumentParser


class WhaleSayJob(ContainerJob):

    def run(self, fileStore):
        """Run `cowsay` with Docker, Singularity or Subprocess."""
        msg = self.call(["cowsay", self.options.msg], check_output=True)
        fileStore.logToMaster(msg)


def main():
    parser = ContainerArgumentParser()
    parser.add_argument("-m", "--msg", default="Hello from the ocean!")
    options = parser.parse_args()
    job = WhaleSayJob(options=options)
    ContainerJob.Runner.startToil(job, options)


if __name__ == "__main__":
    main()
```

Then run:

```bash
# run with docker
whalesay.py jobstore -m 'hello world' --docker docker/whalesay

# run with singularity
whalesay.py jobstore -m 'hello world' --singularity docker://docker/whalesay

# if cowsay is available in the environment
whalesay.py jobstore -m 'hello world'
```

If you want to convert a docker image into a [singularity] image instead of using the `docker://` prefix, check [docker2singularity], and use `-m '/shared-fs-path /shared-fs-path'` to make sure your shared file system is mounted inside the singularity image.

## Contributing

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](.github/CONTRIBUTING.md)! Make sure you add your name to the contributors list:

- 🐋 &nbsp; Juan S. Medina [@jsmedmar](https://github.com/jsmedmar)
- 🐴 &nbsp; Juan E. Arango [@juanesarango](https://github.com/juanesarango)
- 🐒 &nbsp; Max F. Levine [@mflevine](https://github.com/mflevine)
- 🐼 &nbsp; Joe Zhou [@zhouyangyu](https://github.com/zhouyangyu)

## Credits

- This repo was inspired by [toil's][toil_docker] implementation of a `Docker Call` and [toil_vg] [interface][singularity_pr] of `Singularity Calls`.
- This package was initiated with [Cookiecutter] and the [audreyr/cookiecutter-pypackage] project template.

<!-- References -->

[audreyr/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
[bd2kgenomics/toil#2065]: https://github.com/BD2KGenomics/toil/issues/2065
[cookiecutter-toil]: https://github.com/papaemmelab/cookiecutter-toil
[cookiecutter]: https://github.com/audreyr/cookiecutter
[docker2singularity]: https://github.com/singularityware/docker2singularity
[singularity_pr]: https://github.com/BD2KGenomics/toil/pull/1805
[singularity]: http://singularity.lbl.gov/
[toil job class]: http://toil.readthedocs.io/en/latest/developingWorkflows/toilAPI.html#toil.job.Job
[toil_docker]: https://github.com/BD2KGenomics/toil/blob/master/src/toil/lib/docker.py
[toil_vg]: https://github.com/vgteam/toil-vg
[toil]: http://toil.readthedocs.io/
[whalesay]: https://hub.docker.com/r/docker/whalesay/

<!-- Badges -->

[codecov_badge]: https://codecov.io/gh/papaemmelab/toil_container/branch/master/graph/badge.svg
[codecov_base]: https://codecov.io/gh/papaemmelab/toil_container
[gitter_badge]: https://badges.gitter.im/papaemmelab/toil_container/Lobby.svg
[gitter_base]: https://gitter.im/toil_container
[pypi_badge]: https://img.shields.io/pypi/v/toil_container.svg
[pypi_base]: https://pypi.python.org/pypi/toil_container
[pyup_badge]: https://pyup.io/repos/github/papaemmelab/toil_container/shield.svg
[pyup_base]: https://pyup.io/repos/github/papaemmelab/toil_container/
[travis_badge]: https://app.travis-ci.com/papaemmelab/toil_container.svg?branch=master
[travis_base]: https://app.travis-ci.com/papaemmelab/toil_container
[black_badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black_base]: https://github.com/ambv/black
