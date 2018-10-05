"""A custom LSF batchsystem to process additional resources."""
# pylint: disable=C0103, W0223

import base64
import json
import logging
import os
from past.utils import old_div

from toil.batchSystems.lsf import LSFBatchSystem
from toil.batchSystems.lsfHelper import parse_memory_limit
from toil.batchSystems.lsfHelper import parse_memory_resource
from toil.batchSystems.lsfHelper import per_core_reservation

_RESOURCES_START_TAG = '__rsrc'
_RESOURCES_CLOSE_TAG = 'rsrc__'
_PER_SLOT_LSF_CONFIG = 'TOIL_CONTAINER_PER_SLOT'


class CustomLSFBatchSystem(LSFBatchSystem):

    """A custom LSF batchsystem used to encode extra lsf resources."""

    def __init__(self, *args, **kwargs):
        """Create a mapping table for JobIDs to JobNodes."""
        super(CustomLSFBatchSystem, self).__init__(*args, **kwargs)
        self.Id2Node = dict()

    def issueBatchJob(self, jobNode):
        """Load the JobNode into the JobID mapping table."""
        jobID = super(CustomLSFBatchSystem, self).issueBatchJob(jobNode)
        self.Id2Node[jobID] = jobNode
        return jobID

    class Worker(LSFBatchSystem.Worker):

        """Make prepareBsub a class method and parse unitName."""

        def forgetJob(self, jobID):
            """Remove jobNode from the mapping table when forgetting."""
            self.boss.Id2Node.pop(jobID, None)
            return super(CustomLSFBatchSystem.Worker, self).forgetJob(jobID)

        def prepareBsub(self, cpu, mem, jobID):
            """
            Make a bsub commandline to execute.

            Arguments:
                cpu (int): number of cores needed.
                mem (float): number of bytes of memory needed.
                jobID (str): ID number of the job.

            Returns:
                list: a bsub line argument.
            """
            jobNode = self.boss.Id2Node[jobID]
            resources = _decode_dict(jobNode.unitName)
            return build_bsub_line(
                cpu=cpu,
                mem=mem,
                runtime=resources.get('runtime', None),
                jobname='{} {} {}'.format(
                    os.getenv('TOIL_LSF_JOBNAME', 'Toil Job'),
                    jobNode.jobName,
                    jobID))


def build_bsub_line(cpu, mem, runtime, jobname):
    """
    Build an args list for a bsub submission.

    Arguments:
        cpu (int): number of cores needed.
        mem (float): number of bytes of memory needed.
        runtime (int): estimated run time for the job in minutes.
        jobname (str): the job name.

    Returns:
        list: bsub command.
    """
    unique = lambda i: sorted(set(map(str, i)))
    rusage = []
    select = []
    bsubline = [
        'bsub',
        '-cwd', '.',
        '-o', '/dev/null',
        '-e', '/dev/null',
        '-J', "'{}'".format(jobname)]

    if mem:
        if os.getenv(_PER_SLOT_LSF_CONFIG) == 'Y' or per_core_reservation():
            mem = float(mem) / 1024**3 / int(cpu)
        else:
            mem = old_div(float(mem), 1024**3)

        mem = mem if mem >= 1 else 1.0
        mem_resource = parse_memory_resource(mem)
        mem_limit = parse_memory_limit(mem)
        select.append('mem > {}'.format(mem_resource))
        rusage.append('mem={}'.format(mem_resource))
        bsubline += ['-M', str(mem_limit)]

    if cpu:
        bsubline += ['-n', str(int(cpu))]

    if runtime:
        bsubline += ['-W', str(int(runtime))]

    if select:
        bsubline += ['-R', 'select[%s]' % ' && '.join(unique(select))]

    if rusage:
        bsubline += ['-R', 'rusage[%s]' % ' && '.join(unique(rusage))]

    if os.getenv('TOIL_LSF_ARGS'):
        bsubline.extend(os.getenv('TOIL_LSF_ARGS').split())

    # log to lsf
    logger = logging.getLogger(__name__)
    logger.info('Submitting to LSF with: %s', ' '.join(bsubline))

    return bsubline


def _encode_dict(dictionary):
    """Encode `dictionary` in string."""
    if dictionary:
        return '{}{}{}'.format(
            _RESOURCES_START_TAG,
            base64.b64encode(json.dumps(dictionary).encode()).decode(),
            _RESOURCES_CLOSE_TAG)

    return ''


def _decode_dict(string):
    """Get dictionary encoded in `string` by `_encode_dict`."""
    if isinstance(string, str):
        split = string.split(_RESOURCES_START_TAG, 1)[-1]
        split = split.split(_RESOURCES_CLOSE_TAG, 1)

        if len(split) == 2:
            return json.loads(base64.b64decode(split[0]))

    return dict()
