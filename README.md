# Toil Container

[![pypi badge][pypi_badge]][pypi_base]
[![travis badge][travis_badge]][travis_base]
[![pyup badge][pyup_badge]][pyup_base]
[![codecov badge][codecov_badge]][codecov_base]

A python package with a [Toil] Job Class capable of containerized system calls.

This package was built to support the [cookiecutter-toil] repository.

# Features

* 📦 &nbsp; **Installation**

        pip install toil_container

* 🐳  &nbsp; **Containerized System Calls**
`toil_container.ContainerCallJob` inherits from `toil.job.Job`. It has two methods `check_output` and `check_call` that execute commands with either Docker, Singularity or Python's `subprocess`. The Job must be constructed with an `options` argument of the type `argparse.Namespace` that has the attributes `docker` or `singularity` (paths/names of images). If passed, the toil argument `--workDir` is  used as the `/tmp` directory within the containers.

    ```python
    # find_species_origin.py
    from toil_container import ContainerCallJob
    from toil_container import ContainerShortArgumentParser

    class FindOriginJob(ContainerCallJob):

        def run(self, fileStore):
            """find_origin will run with Docker, Singularity or Subprocess."""
            output = self.check_output(["find_origin"])

    options = ContainerShortArgumentParser().parse_args()
    job = jobs.FindOriginJob(options=options)
    ContainerCallJob.Runner.startToil(job, options)
    ```

* ✅ &nbsp; **Container Argument Parser** `toil_container.ContainerArgumentParser` and `toil_container.ContainerShortArgumentParser` add the `--docker`, `--singularity` and `--shared-fs` arguments to the options namespace. `shared-fs` is a path to a shared file system to be mounted within containers.

       darwin$ find_species_origin.py --help

           usage: find_species_origin [-h] [-v] [--help-toil] [TOIL OPTIONAL ARGS] jobStore

           optional arguments:
           -h, --help            show this help message and exit
           --help-toil           print help with full list of Toil arguments and exit

           container arguments:
           --docker              name of the docker image, available in daemon, that will be used for system calls
           --singularity         path of the singularity image that will be used for system calls
           --shared-fs           shared file system path to be mounted in containers

           toil arguments:
           TOIL OPTIONAL ARGS    see --help-toil for a full list of toil parameters
           jobStore              the location of the job store for the workflow [REQUIRED]

* 📘 &nbsp; **A Short Toil Help** `toil_container.ToilShortArgumentParser` only prints the required toil arguments when using `--help`. However, the full list of toil rocketry is printed with `--help-toil`. This is usefull when some of your pipelines users find toil arguments daunting.

       darwin$ hello_world --help

           usage: hello_world [-h] [-v] [--help-toil] [TOIL OPTIONAL ARGS] jobStore

           optional arguments:
           -h, --help            show this help message and exit
           --help-toil           print help with full list of Toil arguments and exit

           toil arguments:
           TOIL OPTIONAL ARGS    see --help-toil for a full list of toil parameters
           jobStore              the location of the job store for the workflow [REQUIRED]

# Contributing

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](CONTROBUTING.md)! Make sure you add your name to the contributors list:

* 🐋 &nbsp; Juan S. Medina [@jsmedmar](https://github.com/jsmedmar)
* 🐴 &nbsp; Juan E. Arango [@juanesarango](https://github.com/juanesarango)
* 🐒 &nbsp; Max F. Levine [@mflevine](https://github.com/mflevine)
* 🐼 &nbsp; Joe Zhou [@zhouyangyu](https://github.com/zhouyangyu)


# Credits

* This repo was inspired by [toil's][toil_docker] implementation of a `Docker Call` and [toil_vg] [interface][singularity_pr] of `Singularity Calls`.
* This package was initiated with [Cookiecutter] and the
[audreyr/cookiecutter-pypackage] project template.

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
