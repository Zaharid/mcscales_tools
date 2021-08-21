# mcscales-tools

Tools for working with Parton Distribution Functions (PDFs) with scale variation
information (`MCscales`), presented in Ref arxiv:XXXXX.
`MCscalesp` grids are Monte Carlo [LHAPDF](https://lhapdf.hepforge.org/) grids
where each replica has been determined using different assumptions on the
renormalisation and factorisation scales on the input data.

The code contains

  - A script to partition an existing MCscales
  - [LHAPDF](https://lhapdf.hepforge.org/) set into
    several new LHAPDF grids, so as to allow computing matched scale variations
    with existing codes (`mcscales-partition-pdf`).
  - A script to generate a new MCscales grid by filtering an existing one by
    excluding particular scale combinations (`mcscales-theory-driven`).

The basic components to extract metadata on scales and manipulate LHAPDF grids
are available as separate functions, which should allow implementing other
scale filtering strategies.

## Installation

This package can be installed with standard Python tooling, using pip. Use

```
pip install mcscales_tools
```

There are no dependencies outside of pip such as LHAPDF python wrappers.

Ir can also be installed from source. To install in development mode, download
the source and use
```
pip install flit
flit install --symlink
```
from the root directory.

### Grid download

The MCscales version 1 PDF set, based on [NNPDF
3.1](https://arxiv.org/abs/1706.00428) can be downloaded from

<https://data.nnpdf.science/pdfs/mcscales_v1.tar.gz>



## Commands


The package contains the `mcscales-partition-pdf` and `mcscales-theory-driven`
commands.

### `mcscales-partition-pdf`

The command splits an original MCscales LHAPDF grid into more grids where scales
are grouped according to the input options.

The first argument is the path to the folder containing the MCscales LHAPDF
grid. If no further arguments are provided the PDF set will be split by
factorisation scale. For example
```
mcscales-partition-pdf mcscales_v1
```
will produce three PDF sets in the current working directory,
`mcscales_v1_kF_1`, `mcscales_v1_kF_0p5` and `mcscales_v1_kF_2` where
the factorisation scale of all of the input data is respectively 1, 0.5, or 2 times the
nominal scale for all input data in the PDF set.

If the optional argument `--split-by-ren-scale` is provided, specifying a
process, then the girds are also split by the renormalisation scale multiplier
of that process. For example
```
mcscales-partition-pdf mcscales_v1 --split-by-ren-scale "DIS CC"
```

Will produce 9 grids including e.g. `mcscales_v1_kF_0p5_kR_DIS_NC_1`, where the
factorisation scale for all replicas is 0.5 and the renormalisation scale for
the DIS CC input data is 0.5 or `mcscales_v1_kF_2_kR_DIS_NC_2` where the
factorisation scale and renormalisation scale for DIS CC data are both 2 (but
the renormalisation scales for other processes can vary among the replicas).



### `mcscales-theory-driven`

The command filters an MCscales grid by filtering combinations according to
certain rules, implementing the legacy concept of "point prescription". The
command takes two arguments: the path to the folder containing the LHAPDF grid,
and the name of the point prescription. The result will be a new LHAPDF gird
with the subset of the replicas from the original that don't contain the vetoed
scaled combinations for each point prescription.

For example

```
mcscales-theory-driven mcscales_v1/ "3 point"
```

Will generate a grid called `mcscales_v1_3_point` in the current directory. This
will contain only the few replicas where all the scale combinations are
"diagonal", that is the renormalisation scale for all processes is the same as
the factorisation scale, as implied by the three point prescription.
The central value will be recomputed appropriately.

More complicated filtering strategies could be implemented by modifying the
[theory_driven.py](https://github.com/Zaharid/mcscales_tools/blob/master/mcscales_tools/theory_driven.py]
file.

The available point prescriptions are:

  - `"3 point"`: Filter all but matching factorisation and renormalisation scales,
    i.e. allow only replicas where all of the pairs of (factorisation,
    renormalisation) scales are one of (0.5, 0.5), (1, 1) or (2, 2) exclude all
    of (0.5, 1.0), (0.5, 2.0), (1.0, 0.5), (1.0, 2.0), (2.0, 0.5), (2.0, 1.0).
  - `"5 point"`: Exclude all of (0.5, 0.5), (0.5, 2.0), (2.0, 0.5), (2.0, 2.0).
  - `"5bar point"` Exclude all of (0.5, 1.0), (1.0, 0.5), (1.0, 2.0), (2.0,
      1.0).
  - `"7 point"`: Exclude all of (0.5, 2.0), (2.0, 0.5).

In addition thee is a `custom` option which will raise an error in an useful
location where the behaviour can be filled by the user, by modifying the source
code.

## Matched scales computations

The `mcscales-partition-pdf` script can be used to compute matched scale
variations across PDF and hard cross section using tools that have no special
knowledge of `MCscales`.

If the user wishes to correlate the factorisation scale variations with a
process included in the PDF fit (for example TOP if computing the ttbar total
cross section), then that process should be passed as argument, e.g.
```
mcscales-partition-pdf mcscales_v1 --split-by-ren-scale TOP
```
Then one produce independent runs with each of the resulting PDFs and scales
matched appropriately. For example the `mcscales_v1_kF_2_kR_TOP_2` would be used
in a run where the scale variation for the ttbar hard cross section is twice the
nominal one, both for factorisation and renormalisation scales.

If the user does not wish to correlate the renormalisation scale variation with
that of any process in the PDF fit (as might be appropriate when e.g. computing
the Higgs cross section) then the PDF should be split by factorisation scale
only
```
mcscales-partition-pdf mcscales_v1
```
and the matched with the hard cross section at that factorisation scale. For
example `mcscales_v1_kF_0p5` would be used in all runs where the Higgs
factorisation scale is 0.5.

Please see the paper with the expressions on how to combine the results of all
the runs to obtain a final PDF+scale uncertainty.


## MCscales grid metadata

The code works by reading the metadata stored in the MCscales grid. The metadata
fields are the following:

### Info file

The LHAPDF info file (e.g. `mcscales_v1.info`) contains the following fields, in
addition to the default ones from LHAPDF:

```yaml
mcscales_processes: ["DIS CC", "DIS NC", "DY", "JETS", "TOP"]
mcscales_scale_multipliers: [0.5, 1, 2]
```

The `mcscales_processes` field specifies the groupings that have been chosen for
the renormalisation scale within each replica: For example all input TOP data was
always fitted with the same renormalisation scale, which however could be is in
general different form the renormalisation scale for JETS within the same
replica. A given replica is always determined with the same factorisation scale
for all the input data (please see the paper for details).

The `mcscales_scale_multipliers` field specifies the possible values for
renormalisation and factorisation scales within any replica.

The values of the fields could change in successive releases.


### Replica files

Each replica member file (e.g. `mcscales_v1_0010.dat`-`mcscales_v1_0823.dat`)
contains the following fields

```yaml
mcscales_ren_multiplier_DIS CC: <NUM>
mcscales_ren_multiplier_DIS NC: <NUM>
mcscales_ren_multiplier_DY: <NUM>
mcscales_ren_multiplier_JETS: <NUM>
mcscales_ren_multiplier_TOP: <NUM>
mcscales_fac_multiplier: <NUM>
```

where the possible values of `<NUM>` are the values of
`mcscales_scale_multipliers` above (currently 0.5, 1 or 2) and the keys
corresponding to renormalization scales are constructed by prepending the string
`mcscales_ren_multiplier_` to each of the values in `mcscales_processes`.

These values can be read by parsing the YAML headers appropriately (as this code
does). Using the LHAPDF python interface, **not** provided by this code, the
metadata can be read as follows
```python
>>> import lhapdf
>>> replica = 84
>>> pdf_replica = lhapdf.mkPDF("mcscales_v1", replica)
mcscales_v1 PDF set, member #84, version 1
>>> pdf_replica.info().get_entry("mcscales_processes")
['DIS CC', 'DIS NC', 'DY', 'JETS', 'TOP']
>>> pdf_replica.info().get_entry("mcscales_ren_multiplier_DIS CC")
0.5
```

## Citation

Please cite arxiv:XXXXX
