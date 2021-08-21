"""Script to obtain LHAPDF grids from an MCscales PDF set, where the PDF
replicas are split by their scale choices. The default behaviour is to split
the replicas by the factorisation scale only, i.e. three separate PDF sets will
be generated (one with the central scale, one with the scale halved, and one
with the scale doubled). To also split the replicas by the renormalisation
scale of a particular process, one can use the --split_by_ren_scale flag,
followed by the process whose renormalisation scale is of interest.

For example, to split by both the factorisation scale and the renormalisation
scale used for top quark data, one would run


The processes by which one can select the renormalisation scales are DIS NC,
DIS CC, DY, JETS and TOP.  The resulting PDF sets are put in your LHAPDF
path."""

import argparse
import logging
import sys
import pathlib

from .checks import CheckError, check_is_valid_mcscales
from .vendor.lhio import SimplePDFWrapper, new_pdf_from_indexes
from .grouping import group_by_fac, group_by_fac_and_ren

logging.basicConfig(level=logging.INFO, format='[%(levelname)s]: %(message)s')

log = logging.getLogger()


def process_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Example: `mcscales-partition-pdf mcscales_v1/ --split_by_ren_scale TOP`",
    )
    parser.add_argument(
        "pdf", help="The name of the PDF set to split up by scales.",
    )
    parser.add_argument(
        "--split-by-ren-scale",
        help="""Split the replicas by the factorisation and the renormalisation scale of a specified process.
                One must then specify a process which they want to split the renormalisation scales by.
                This can be one of DIS NC, DIS CC, DY, JETS, TOP""",
    )
    args = parser.parse_args()
    return args


def grids_from_fac_partitions(pdf, partitions):
    newnames = []
    descs = []
    for fac, indexes in partitions.items():
        if int(fac) == fac:
            fac = int(fac)
        sfac = str(fac).replace(".", "p")
        newname = f"{pdf.name}_kF_{sfac}"
        newnames.append(newname)
        if pathlib.Path(newname).exists():
            raise CheckError(
                f"Path {newname} already exsits. Please delete before proceeding"
            )
        descs.append(
            f"MCscales set derived from '{pdf.name}', with all factorisation scales equal to {fac}."
        )
        log.info(f"Found {len(indexes)} replicas for grid {newname}")

    # The double loop is so we can check before proceeding.
    for (fac, indexes), newname, desc in zip(partitions.items(), newnames, descs):
        new_pdf_from_indexes(
            pdf, indexes, newname, description=desc,
        )


def grids_from_fac_ren_partitions(pdf, partitions, process):
    newnames = []
    descs = []
    for (fac, ren), indexes in partitions.items():
        if int(fac) == fac:
            fac = int(fac)
        if int(ren) == ren:
            ren = int(ren)
        sfac = str(fac).replace(".", "p")
        sren = str(ren).replace(".", "p")
        newname = f"{pdf.name}_kF_{sfac}_kR_{process.replace(' ', '_')}_{sren}"
        newnames.append(newname)
        if pathlib.Path(newname).exists():
            raise CheckError(
                f"Path {newname} already exsits. Please delete before proceeding"
            )
        log.info(f"Found {len(indexes)} replicas for grid {newname}")
        descs.append(
            f"MCscales set derived from '{pdf.name}', with all factorisation scales equal to {fac} and"
            f" all renormalisation scales for process {process} set to {ren}."
        )

    for (fac, indexes), newname, desc in zip(partitions.items(), newnames, descs):
        new_pdf_from_indexes(
            pdf, indexes, newname, description=desc,
        )


def main():
    try:
        args = process_args()
        pdf = SimplePDFWrapper(args.pdf)
        check_is_valid_mcscales(pdf)
        process = args.split_by_ren_scale
        if process is None:
            log.info(f"Splitting {pdf.name} by factorisation scale")
            partitions = group_by_fac(pdf)
            grids_from_fac_partitions(pdf, partitions)
        else:
            valid = pdf.info["mcscales_processes"]
            if process not in valid:
                raise CheckError(
                    f"Invalid process. For {pdf.name}, the valid choices are {valid}. Got '{process}''"
                )

            log.info(
                f"Splitting {pdf.name} by renormalisation scale of {process} and factorisation scale"
            )
            partitions = group_by_fac_and_ren(pdf, process)
            grids_from_fac_ren_partitions(pdf, partitions, process)
    except CheckError as e:
        log.error(f"Error processing script: {e}")
        sys.exit(1)
    except Exception as e:
        log.exception("Unexpected error ocurred. Please report it")
        raise
