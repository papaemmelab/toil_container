# Toil Container

[![pypi badge][pypi_badge]][pypi_base]
[![travis badge][travis_badge]][travis_base]
[![pyup badge][pyup_badge]][pyup_base]
[![codecov badge][codecov_badge]][codecov_base]

A python package with a [Toil] Job Class capable of containerized system calls.

This package was built to support the [cookiecutter-toil] repository.

## Features

* 📦 &nbsp; **Easy Installation**

        pip install toil_container

* 🛳  &nbsp; **Container Job Class**

    `toil_container.ContainerJob` is a Toil job class with a `call` method that executes commands with either `Docker`, `Singularity` or Python's `subprocess` depending on image availability. The Job must be constructed with an `options` argument of the type `argparse.Namespace` that has attributes `docker_image` or `singularity_image`. If passed, the toil argument `--workDir` is used as the `/tmp` directory within the containers.

    ```python
    # find_species_origin.py
    from toil_container import ContainerJob
    from toil_container import ContainerArgumentParser


    class FindOriginJob(ContainerJob):

        def run(self, fileStore):
            """find_origin will run with Docker, Singularity or Subprocess."""
            status = self.call(["find_origin"], check_output=False)
            output = self.call(["find_origin"], check_output=True)


    def main():
        options = ContainerArgumentParser().parse_args()
        job = FindOriginJob(options=options)
        ContainerJob.Runner.startToil(job, options)

    if __name__ == "__main__":
        main()
    ```

    Then to run with singularity simply do (or docker):

        find_species_origin.py
            --container-volumes <local-path> <container-path>
            --singularity-image docker://ubuntu
            jobstore

* 📘 &nbsp; **Argument Parser With Shortened Toil Options**

    `toil_container.ContainerArgumentParser` adds the `--docker-image`, `--singularity-image` and `--container-volumes` arguments to the options namespace. This parser only prints the required toil arguments when using `--help`. However, the full list of toil rocketry is printed with `--help-toil`. If you don't need the container options but want to use `--help-toil` use `toil_container.ToilShortArgumentParser`.

       darwin$ find_species_origin.py --help

           usage: find_species_origin [-h] [-v] [--help-toil] [TOIL OPTIONAL ARGS] jobStore

            optional arguments:
            -h, --help            show this help message and exit
            --help-toil           print help with full list of Toil arguments and exit

            container arguments:
            --docker-image        name/path of the docker image available in daemon
            --singularity-image   name/path of the singularity image available in deamon
            --container-volumes   tuples of (local path, absolute container path)

            toil arguments:
            TOIL OPTIONAL ARGS    see --help-toil for a full list of toil parameters
            jobStore              the location of the job store for the workflow [REQUIRED]

* 🐳  &nbsp; **Container System Calls**

     `docker_call` and `singularity_call` are functions that make containerized system calls. Both functions have the same calling signature. They can return the output or the exit code by setting `check_output=True` or `False`. You can alse set the `env`, `cwd`, `volumes` and `working_dir` for the container call. `working_dir` is set as the `/tmp` directory inside the container.

    ```python
    from toil_container import singularity_call

    image = "docker://ubuntu:latest"
    status = singularity_call(image, ["echo", "hello world"])
    output = singularity_call(image, ["echo", "hello world"], check_output=True)
    ```

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
[toil_docker]: https://github.com/BD2KGenomics/toil/blob/master/src/toil/lib/docker.py
[toil_vg]: https://github.com/vgteam/toil-vg
[singularity_pr]: https://github.com/BD2KGenomics/toil/pull/1805
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[audreyr/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
[toil]: http://toil.readthedocs.io/
[cookiecutter-toil]: https://github.com/leukgen/cookiecutter-toil

<!-- Badges -->
[codecov_badge]: https://codecov.io/gh/leukgen/toil_container/branch/master/graph/badge.svg
[codecov_base]: https://codecov.io/gh/leukgen/toil_container
[pypi_badge]: https://img.shields.io/pypi/v/toil_container.svg
[pypi_base]: https://pypi.python.org/pypi/toil_container
[pyup_badge]: https://pyup.io/repos/github/leukgen/toil_container/shield.svg
[pyup_base]: https://pyup.io/repos/github/leukgen/toil_container/
[travis_badge]: https://img.shields.io/travis/leukgen/toil_container.svg
[travis_base]: https://travis-ci.org/leukgen/toil_container
