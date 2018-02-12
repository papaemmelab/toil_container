# Toil Container

[![pypi](https://img.shields.io/pypi/v/toil_container.svg)](https://pypi.python.org/pypi/toil_container)
[![build](https://img.shields.io/travis/leukgen/toil_container.svg)](https://travis-ci.org/leukgen/toil_container)
[![updates](https://pyup.io/repos/github/leukgen/toil_container/shield.svg)](https://pyup.io/repos/github/leukgen/toil_container/)


A python package with a [Toil] Job Class capable of containerized system calls.

This package was built to support the [cookiecutter-toil] repository.

# Features

* **A Short Toil Help** 📘 `toil_container.ToilShortArgumentParser` only prints the required toil arguments when using `--help`. However, the full list of toil rocketry is printed with `--help-toil`. This is usefull when some of your pipelines users find toil arguments daunting.

        darwin$ hello_world --help

            usage: hello_world [-h] [-v] [--help-toil] [TOIL OPTIONAL ARGS] jobStore

            optional arguments:
            -h, --help            show this help message and exit
            --help-toil           print help with full list of Toil arguments and exit

            toil arguments:
            TOIL OPTIONAL ARGS    see --help-toil for a full list of toil parameters
            jobStore              the location of the job store for the workflow [REQUIRED]


* **Containerized System Calls** 🐳 `toil_container.ContainerCallJob` is a `Job` class with two abstract methods `check_output` and `check_call` that will be executed with either Docker, Singularity or Python's `subprocess`. The Job must be constructed with an `options` argument of the type `argparse.Namespace` that has the attributes `docker` or `singularity`. If passed, the toil argument `--workDir` will be used as the `/tmp` directory within the containers.

    ```python
    # find_species_origin.py
    import toil_container

    class FindOriginJob(toil_container.ContainerCallJob):

        def run(self, fileStore):
            """find_origin will run with Docker, Singularity or Subprocess."""
            output = self.check_output(["find_origin"])

    parser = toil_container.ToilContainerHelpParser()
    job = jobs.FindOriginJob(options=options)
    toil_container.ContainerCallJob.Runner.startToil(job, options)
    ```

* **Container Argument Parser** ✅ `toil_container.ToilContainerArgumentParser` and `toil_container.ToilContainerShortArgumentParser` add the `--docker`, `--singularity` and `--shared-fs` arguments to the options namespace. `shared-fs` is a path to a shared file system to be mounted within containers.

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

# Contributing

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](CONTROBUTING.md)!

# Credits

This package was initiated with [Cookiecutter] and the
[audreyr/cookiecutter-pypackage] project template.

<!-- References -->

[Cookiecutter]: https://github.com/audreyr/cookiecutter
[audreyr/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
[Toil]: http://toil.readthedocs.io/
[cookiecutter-toil]: https://github.com/leukgen/cookiecutter-toil
