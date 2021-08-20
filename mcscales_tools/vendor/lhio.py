"""
A module that reads and writes LHAPDF grids.

This module is taken from the NNPDF repository


https://github.com/NNPDF/nnpdf


and modified slightly so as to be standalone (in particular not requiring
either the LHAPDF or NNPDF wrappers) and with a few fewer functions.
"""

import logging
import os.path as osp
import pathlib
import shutil

import numpy as np
import pandas as pd

from .compat import yaml


log = logging.getLogger(__name__)


class SimplePDFWrapper:
    def __init__(self, path):
        path = pathlib.Path(path)
        if not path.is_dir():
            raise FileNotFoundError(
                f"Expecting the path {path} to be a directory on the filesystem"
            )
        self.path = path
        self._info = None

    def is_valid(self):
        return (
            self.path.is_dir()
            and self.infopath.is_file()
            and self.member_path(0).is_file()
        )

    @property
    def name(self):
        return self.path.name

    @property
    def infopath(self):
        return self.path / f"{self.name}.info"

    def member_path(self, member_id):
        suffix = str(member_id).zfill(4)
        return self.path / f"{self.name}_{suffix}.dat"

    def header(self, member_id):
        path = self.member_path(member_id)
        y = yaml.YAML()
        with open(path, "rb") as f:
            # This is very slow for some reason
            # return next(iter(y.load_all(f)))
            return y.load(b"".join(split_sep(f)))

    @property
    def info(self):
        if self._info is not None:
            return self._info
        y = yaml.YAML()
        with open(self.infopath) as f:
            info = y.load(f)

        self._info = info
        return info

    def __len__(self):
        return self.info["NumMembers"]


def split_sep(f):
    for line in f:
        if line.startswith(b'---'):
            break
        yield line


def read_xqf_from_file(f):

    lines = split_sep(f)
    try:
        (xtext, qtext, ftext) = [next(lines) for _ in range(3)]
    except StopIteration:
        return None
    xvals = np.fromstring(xtext, sep=" ")
    qvals = np.fromstring(qtext, sep=" ")
    fvals = np.fromstring(ftext, sep=" ", dtype=np.int)
    vals = np.fromstring(b''.join(lines), sep=" ")
    return pd.Series(vals, index=pd.MultiIndex.from_product((xvals, qvals, fvals)))


def read_all_xqf(f):
    while True:
        result = read_xqf_from_file(f)
        if result is None:
            return
        yield result


def load_replica(pdf, rep):

    path = pdf.member_path(rep)

    log.debug("Loading replica {rep} at {path}".format(rep=rep, path=path))

    with open(path, 'rb') as inn:
        header = b"".join(split_sep(inn))
        xfqs = list(read_all_xqf(inn))
        xfqs = pd.concat(xfqs, keys=range(len(xfqs)))
    return header, xfqs


# Split this to debug easily
def _rep_to_buffer(out, header, subgrids):
    sep = b'---'
    out.write(header)
    out.write(sep)
    for _, g in subgrids.groupby(level=0):
        out.write(b'\n')
        ind = g.index.get_level_values(1).unique()
        np.savetxt(out, ind, fmt='%.7E', delimiter=' ', newline=' ')
        out.write(b'\n')
        ind = g.index.get_level_values(2).unique()
        np.savetxt(out, ind, fmt='%.7E', delimiter=' ', newline=' ')
        out.write(b'\n')
        # Integer format
        ind = g.index.get_level_values(3).unique()
        np.savetxt(out, ind, delimiter=' ', fmt="%d", newline=' ')
        out.write(b'\n ')
        # Reshape so printing is easy
        reshaped = g.values.reshape(
            (len(g.groupby(level=1)) * len(g.groupby(level=2)), len(g.groupby(level=3)))
        )
        np.savetxt(out, reshaped, delimiter=" ", newline="\n", fmt='%14.7E')
        out.write(sep)


def write_replica(rep, set_root, header, subgrids):
    suffix = str(rep).zfill(4)
    target_file = set_root / f'{set_root.name}_{suffix}.dat'
    if target_file.is_file():
        log.warning(f"Overwriting replica file {target_file}")
    with open(target_file, 'wb') as out:
        _rep_to_buffer(out, header, subgrids)


def big_matrix(gridlist):
    """Return a properly indexes matrix of the differences between each member
    and the central value"""
    central_value = gridlist[0]
    X = pd.concat(
        gridlist[1:],
        axis=1,
        keys=range(1, len(gridlist) + 1),  # avoid confusion with rep0
    ).subtract(central_value, axis=0)
    if np.any(X.isnull()) or X.shape[0] != len(central_value):
        raise ValueError("Incompatible grid specifications")
    return X


def rep_matrix(gridlist):
    """Return a properly indexes matrix of all the members"""
    X = pd.concat(
        gridlist, axis=1, keys=range(1, len(gridlist) + 1),  # avoid confusion with rep0
    )
    if np.ravel(pd.isnull(X)).any():
        raise ValueError("Found null values in grid")
    return X


def _index_to_path(set_folder, set_name, index):
    return set_folder / ('%s_%04d.dat' % (set_name, index))


def generate_replica0(pdf, extra_fields=None):
    """ Generates a replica 0 as an average over an existing set of LHAPDF
        replicas and outputs it to the PDF's parent folder

    Parameters
    -----------
    pdf : validphys.core.PDF
        An existing validphys PDF object from which the average replica will be
        (re-)computed

    """

    log.info(f"Generating replica 0 for {pdf.name}")

    if extra_fields is not None:
        raise NotImplementedError()

    set_info = pathlib.Path(pdf.infopath)
    set_root = set_info.parent
    if not set_root.exists():
        raise RuntimeError(f"Target directory {set_root} does not exist")

    loaded_grids = {}
    grids = []

    for irep in range(1, len(pdf)):
        if irep in loaded_grids:
            grid = loaded_grids[irep]
        else:
            _header, grid = load_replica(pdf, irep)
            loaded_grids[irep] = grid
        grids.append(grid)
    # This takes care of failing if headers don't match
    try:
        M = rep_matrix(grids)
    except ValueError as e:
        raise ValueError(
            "Null values found in replica grid matrix. "
            "This may indicate that the headers don't match"
        ) from e
    header = b'PdfType: central\nFormat: lhagrid1\n'
    write_replica(0, set_root, header, M.mean(axis=1))


def new_pdf_from_indexes(
    pdf, indexes, set_name, folder=None, extra_fields=None, description=None
):
    """Create a new PDF set from by selecting replicas from another one.

    Parameters
    -----------
    pdf : validphys.core.PDF
        An existng validphys PDF object from which the indexes will be
        selected.
    indexes : Iterable[int]
        An iterable with integers corresponding to files in the LHAPDF set.
        Note that replica 0 will be calculated for you as the mean of the
        selected replicas.
    set_name : str
        The name of the new PDF set.
    folder : str, bytes, os.PathLike
        The path where the LHAPDF set will be written. Must exsist.
    """

    if folder is None:
        folder = pathlib.Path()

    set_root = folder / set_name
    if set_root.exists():
        raise FileExistsError(
            f"Target directory {set_root} already exists. Delete it before proceeding."
        )

    set_root.mkdir()

    original_info = pathlib.Path(pdf.infopath)
    original_folder = original_info.parent

    new_len = len(indexes) + 1

    log.info(f"Writing new LHAPDF grid with {new_len} members at {set_root}.")

    new_info = pdf.info.copy()
    new_info["NumMembers"] = new_len

    if extra_fields:
        new_info.update(extra_fields)

    if description is not None:
        new_info["SetDesc"] = description

    new_info_path = set_root / (set_name + '.info')

    with new_info_path.open('w') as new_file:
        yaml.YAML().dump(new_info, new_file)

    for newindex, oldindex in enumerate(indexes, 1):
        original_path = _index_to_path(original_folder, pdf.name, oldindex)
        new_path = _index_to_path(set_root, set_name, newindex)
        shutil.copy(original_path, new_path)

    generated_pdf = SimplePDFWrapper(set_root)
    generate_replica0(generated_pdf)
