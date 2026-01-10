# IS2view

Interactive visualization and data extraction tool for ICESat-2 ATL14/15 Gridded Land Ice Height Products

## About

<table>
  <tr>
    <td><b>Version:</b></td>
    <td>
        <a href="https://pypi.python.org/pypi/IS2view/" alt="PyPI"><img src="https://img.shields.io/pypi/v/IS2view.svg"></a>
        <a href="https://anaconda.org/conda-forge/is2view" alt="conda-forge"><img src="https://img.shields.io/conda/vn/conda-forge/is2view"></a>
        <a href="https://github.com/tsutterley/IS2view/releases/latest" alt="commits-since"><img src="https://img.shields.io/github/commits-since/tsutterley/IS2view/latest"></a>
    </td>
  </tr>
  <tr>
    <td><b>Citation:</b></td>
    <td>
        <a href="https://doi.org/10.5281/zenodo.8015463" alt="zenodo"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.8015463.svg"></a>
    </td>
  </tr>
  <tr>
    <td><b>Tests:</b></td>
    <td>
        <a href="https://is2view.readthedocs.io/en/latest/?badge=latest" alt="Documentation Status"><img src="https://readthedocs.org/projects/is2view/badge/?version=latest"></a>
        <a href="https://github.com/tsutterley/IS2view/actions/workflows/python-request.yml" alt="Build"><img src="https://github.com/tsutterley/IS2view/actions/workflows/python-request.yml/badge.svg"></a>
        <a href="https://github.com/tsutterley/IS2view/actions/workflows/ruff-format.yml" alt="Ruff"><img src="https://github.com/tsutterley/IS2view/actions/workflows/ruff-format.yml/badge.svg"></a>
    </td>
  </tr>
  <tr>
    <td><b>Data:</b></td>
    <td>
        <a href="https://nsidc.org/data/ATL14/" alt="ATL14"><img src="https://img.shields.io/badge/NSIDC-ATL14-15536d"></a>
        <a href="https://nsidc.org/data/ATL15/" alt="ATL15"><img src="https://img.shields.io/badge/NSIDC-ATL15-15536d"></a>
    </td>
  </tr>
  <tr>
    <td><b>License:</b></td>
    <td>
        <a href="https://github.com/tsutterley/IS2view/blob/main/LICENSE" alt="License"><img src="https://img.shields.io/github/license/tsutterley/IS2view"></a>
    </td>
  </tr>
</table>

For more information: see the documentation at [is2view.readthedocs.io](https://is2view.readthedocs.io/) or the ICESat-2 websites at [Goddard Space Flight Center](https://icesat-2.gsfc.nasa.gov) or the [National Snow and Ice Data Center](https://nsidc.org/data/icesat-2/)


## Installation

From PyPI:

```bash
python3 -m pip install IS2view
```

To include all optional dependencies:

```bash
python3 -m pip install IS2view[all]
```

Using `conda` or `mamba` from conda-forge:

```bash
conda install -c conda-forge is2view
```

```bash
mamba install -c conda-forge is2view
```

Development version from GitHub:

```bash
python3 -m pip install git+https://github.com/tsutterley/IS2view.git
```

### Running with Pixi

Alternatively, you can use [Pixi](https://pixi.sh/) for a streamlined workspace environment:

1. Install Pixi following the [installation instructions](https://pixi.sh/latest/#installation)
2. Clone the project repository:

```bash
git clone https://github.com/tsutterley/IS2view.git
```

3. Move into the `IS2view` directory

```bash
cd IS2view
```

4. Install dependencies and start JupyterLab:

```bash
pixi run start
```

This will automatically create the environment, install all dependencies, and launch JupyterLab in the [notebooks](./doc/source/notebooks/) directory.

## Dependencies

- [dask: Parallel computing with task scheduling](https://www.dask.org/)
- [geopandas: Python tools for geographic data](http://geopandas.readthedocs.io/)
- [h5netcdf: Pythonic interface to netCDF4 via h5py](https://h5netcdf.org/)
- [ipyleaflet: Interactive maps in the Jupyter notebook](https://ipyleaflet.readthedocs.io/en/latest/)
- [matplotlib: Python 2D plotting library](https://matplotlib.org/)
- [numpy: Scientific Computing Tools For Python](https://www.numpy.org)
- [rasterio: Access to geospatial raster data](https://rasterio.readthedocs.io/en/latest/)
- [rioxarray: geospatial xarray extension powered by rasterio](https://github.com/corteva/rioxarray)
- [xarray: N-D labeled arrays and datasets in Python](https://docs.xarray.dev/en/stable/) 

## Download

The program homepage is:  
<https://github.com/tsutterley/IS2view>

A zip archive of the latest version is available directly at:  
<https://github.com/tsutterley/IS2view/archive/main.zip>

## Disclaimer

This package includes software developed at NASA Goddard Space Flight Center (GSFC) and the University of Washington Applied Physics Laboratory (UW-APL).
It is not sponsored or maintained by the Universities Space Research Association (USRA), AVISO or NASA.
The software is provided here for your convenience but *with no guarantees whatsoever*.

## Contributing

This project contains work and contributions from the [scientific community](./CONTRIBUTORS.md).
If you would like to contribute to the project, please have a look at the [contribution guidelines](./doc/source/getting_started/Contributing.rst), [open issues](https://github.com/tsutterley/IS2view/issues) and [discussions board](https://github.com/tsutterley/IS2view/discussions).

## License

The content of this project is licensed under the [Creative Commons Attribution 4.0 Attribution license](https://creativecommons.org/licenses/by/4.0/) and the source code is licensed under the [MIT license](LICENSE).
