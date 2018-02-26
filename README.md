# Toil Container

[![pypi badge][pypi_badge]][pypi_base]
[![travis badge][travis_badge]][travis_base]
[![pyup badge][pyup_badge]][pyup_base]
[![codecov badge][codecov_badge]][codecov_base]

A python package with container support for [Toil] pipelines.

Check the [example](#usage)! This package was built to support the [cookiecutter-toil] repository.

## Features

* 📦 &nbsp; **Easy Installation**

        pip install toil_container

* 🐳  &nbsp; **Container System Calls**

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

* 🛳  &nbsp; **Container Job Class**

    `ContainerJob` is a [Toil Job Class] with a `call` method that executes commands with either `Docker`, `Singularity` or `Subprocess` depending on image availability. Check out this simple [whalesay example](#usage)! The Job must be constructed with an `options` argument of the type `argparse.Namespace` that may have the following attributes:

    | attribute             | action                  | description             |
    | --------------------- | ----------------------- | ----------------------- |
    | `options.docker`      | use docker              | name or path to image   |
    | `options.singularity` | use singularity         | name or path to image   |
    | `options.workDir`     | set as container `/tmp` | path to work directory  |
    | `options.volumes`     | volumes to be mounted   | list of src, dst tuples |

* 📘 &nbsp; **Container Parser With Short Toil Options**

    `ContainerArgumentParser` adds the `--docker`, `--singularity` and `--volumes` arguments to the options namespace. This parser only prints the required toil arguments when using `--help`. However, the full list of toil rocketry is printed with `--help-toil`. If you don't need the container options but want to use `--help-toil` use `ToilShortArgumentParser`.

       whalesay.py --help

           usage: whalesay [-h] [-v] [--help-toil] [TOIL OPTIONAL ARGS] jobStore

            optional arguments:
            -h, --help            show this help message and exit
            --help-toil           print help with full list of Toil arguments and exit

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

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](CONTROBUTING.md)! Make sure you add your name to the contributors list:

* 🐋 &nbsp; Juan S. Medina [@jsmedmar](https://github.com/jsmedmar)
* 🐴 &nbsp; Juan E. Arango [@juanesarango](https://github.com/juanesarango)
* 🐒 &nbsp; Max F. Levine [@mflevine](https://github.com/mflevine)
* 🐼 &nbsp; Joe Zhou [@zhouyangyu](https://github.com/zhouyangyu)

## Credits

* This repo was inspired by [toil's][toil_docker] implementation of a `Docker Call` and [toil_vg] [interface][singularity_pr] of `Singularity Calls`.
* This package was initiated with [Cookiecutter] and the [audreyr/cookiecutter-pypackage] project template.

<!-- References -->
[audreyr/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
[cookiecutter-toil]: https://github.com/leukgen/cookiecutter-toil
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[docker2singularity]: https://github.com/singularityware/docker2singularity
[singularity_pr]: https://github.com/BD2KGenomics/toil/pull/1805
[singularity]: http://singularity.lbl.gov/
[toil job class]: http://toil.readthedocs.io/en/latest/developingWorkflows/toilAPI.html#toil.job.Job
[toil_docker]: https://github.com/BD2KGenomics/toil/blob/master/src/toil/lib/docker.py
[toil_vg]: https://github.com/vgteam/toil-vg
[toil]: http://toil.readthedocs.io/
[whalesay]: https://hub.docker.com/r/docker/whalesay/

<!-- Badges -->
[codecov_badge]: https://codecov.io/gh/leukgen/toil_container/branch/master/graph/badge.svg
[codecov_base]: https://codecov.io/gh/leukgen/toil_container
[pypi_badge]: https://img.shields.io/pypi/v/toil_container.svg
[pypi_base]: https://pypi.python.org/pypi/toil_container
[pyup_badge]: https://pyup.io/repos/github/leukgen/toil_container/shield.svg
[pyup_base]: https://pyup.io/repos/github/leukgen/toil_container/
[travis_badge]: https://img.shields.io/travis/leukgen/toil_container.svg
[travis_base]: https://travis-ci.org/leukgen/toil_container
