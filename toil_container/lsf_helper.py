"""
Adapted from toil.batchSystems.lsfHelper.

https://github.com/DataBiosphere/toil/blob/master/src/toil/batchSystems/lsfHelper.py.
"""
from toil.lib.conversions import convert_units
from toil.batchSystems.lsfHelper import get_lsf_units
from toil.batchSystems.lsfHelper import per_core_reservation

# Run this functions once and not on every job
LSF_UNIT = get_lsf_units()
PER_CORE = per_core_reservation()


def parse_memory(mem: float) -> str:
    """Parse memory parameter."""
    megabytes_of_mem = convert_units(float(mem), src_unit=LSF_UNIT, dst_unit="MB")
    if megabytes_of_mem < 1:
        megabytes_of_mem = 1.0
    # round as a string here to avoid returning something like 1.231e+12
    return f"{megabytes_of_mem:.0f}MB"
