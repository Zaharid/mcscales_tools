"""Tools for wroking with LHAPDF grids with MCScales (arxiv:xxxx)"""
__version__ = "1.0"

try:
    import lhapdf
except ImportError as e:
    raise ImportError(
        """The LHAPDF python wrappers could not be found in the environment. We suggest installing them using the conda  system with the command:

    conda install lhapdf -c https://packages.nnpdf.science/public

Alternaitvely, please check

    https://lhapdf.hepforge.org/install.html

for instrctions."""
    ) from e
