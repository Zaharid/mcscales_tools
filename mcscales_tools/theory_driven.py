"""Script to obtain LHAPDF grids from an MCscales PDF set, where the PDF
replicas are selected according to a particular point prescription. For
example, if '7 point' is chosen, then all replicas with any scale combinations
where one scale multiplier is 2 and one is 0.5 are discarded.
"""
import argparse
import logging
import sys
import pathlib

from .vendor.lhio import new_pdf_from_indexes, SimplePDFWrapper
from .grouping import drop_bad_combinations
from .checks import check_is_valid_mcscales, CheckError

logging.basicConfig(level=logging.INFO, format='[%(levelname)s]: %(message)s')

log = logging.getLogger()

badscales_dict = {
    "3 point": [(0.5, 1.0), (0.5, 2.0), (1.0, 0.5), (1.0, 2.0), (2.0, 0.5), (2.0, 1.0)],
    "5 point": [(0.5, 0.5), (0.5, 2.0), (2.0, 0.5), (2.0, 2.0)],
    "5bar point": [(0.5, 1.0), (1.0, 0.5), (1.0, 2.0), (2.0, 1.0)],
    "7 point": [(0.5, 2.0), (2.0, 0.5)],
}


def process_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Example:\n mcscales-theory-driven /path/to/mcscales_v1 '3 point'",
    )
    parser.add_argument(
        "pdf", help="The path of the MCscales LHAPDF set to use as input.",
    )
    parser.add_argument(
        "point_prescription",
        choices=["3 point", "5 point", "5bar point", "7 point", "custom"],
        help="Discard replicas according to scale combinations that are"
        "disallowed by the given point prescription.",
    )
    args = parser.parse_args()
    return args


def partition_by_scales(pdf, point_prescription):
    return drop_bad_combinations(pdf, badscales_dict[point_prescription])


def main():
    try:
        args = process_args()
        pdf = SimplePDFWrapper(args.pdf)
        check_is_valid_mcscales(pdf)
        pp = args.point_prescription
        newname = f"{pdf.name}_{pp.replace(' ', '_')}"
        if pathlib.Path(newname).exists():
            raise CheckError(
                f"Path '{newname}' already exists. Please delete it first."
            )
        log.info(f"Finding replicas in {pdf.name} compatible with '{pp}'")
        if pp == "custom":
            raise RuntimeError("Modify the code here to implement custom behaviour")
        indexes = partition_by_scales(pdf, pp)
        if not indexes:
            raise CheckError("No replicas satisfy the constraint")
        log.info(f"Found {len(indexes)} replicas satisfying the condition.")
        new_pdf_from_indexes(
            pdf,
            indexes,
            newname,
            description=f"MCscales PDF resulting from filtering {pdf.name} so as to conform to the {pp} prescription.",
        )
        log.info(f"New grid {newname} created successfully.")
        print(newname)
    except CheckError as e:
        log.error(f"Error processing script: {e}")
        sys.exit(1)
    except Exception as e:
        log.exception("Unexpected error ocurred. Please report it")
        raise
