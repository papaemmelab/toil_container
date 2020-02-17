"""Custom singleMachine batch system."""

from threading import Thread

from toil.batchSystems.singleMachine import SingleMachineBatchSystem


class SingleMachineBatchSystem(SingleMachineBatchSystem):

    """A singleMachine batch system that """

    def __init__(self, config, maxCores, maxMemory, maxDisk):
        """Fake debugWorker and create only 5 threads."""
        config.debugWorker = True

        super(SingleMachineBatchSystem, self).__init__(
            config, maxCores, maxMemory, maxDisk
        )

        for _ in range(5):
            worker = Thread(target=self.worker, args=(self.inputQueue,))
            self.workerThreads.append(worker)
            worker.start()
