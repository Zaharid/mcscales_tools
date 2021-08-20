from collections import defaultdict
from .vendor.lhio import SimplePDFWrapper


def group_by_fac(pdf):
    d = defaultdict(list)
    for i in range(1, len(pdf)):
        header = pdf.header(i)
        fac = header["mcscales_fac_multiplier"]
        d[fac].append(i)
    return dict(d)


def group_by_fac_and_ren(pdf, process):
    d = defaultdict(list)
    process_key = "mcscales_ren_multiplier_" + process
    for i in range(1, len(pdf)):
        header = pdf.header(i)
        fac = header["mcscales_fac_multiplier"]
        ren = header[process_key]
        d[(fac, ren)].append(i)
    return dict(d)


def _check_banned(processes, header, banned_pairs):
    fac = header["mcscales_fac_multiplier"]
    for process in processes:
        process_key = "mcscales_ren_multiplier_" + process
        ren = header[process_key]
        if (fac, ren) in banned_pairs:
            return False
    return True


def drop_bad_combinations(pdf, banned_pairs):
    surviving = []
    processes = pdf.info["mcscales_processes"]
    for i in range(1, len(pdf)):
        header = pdf.header(i)
        if _check_banned(processes, header, banned_pairs):
            surviving.append(i)
    return surviving
