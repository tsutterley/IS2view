"""
io.py
Written by Tyler Sutterley (06/2024)
Utilities for reading gridded ICESat-2 files using rasterio and xarray

PYTHON DEPENDENCIES:
    h5netcdf: Pythonic interface to netCDF4 via h5py
        https://h5netcdf.org/
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    rasterio: Access to geospatial raster data
        https://github.com/rasterio/rasterio
        https://rasterio.readthedocs.io
    rioxarray: geospatial xarray extension powered by rasterio
        https://github.com/corteva/rioxarray
    xarray: N-D labeled arrays and datasets in Python
        https://docs.xarray.dev/en/stable/

UPDATE HISTORY:
    Updated 06/2024: use wrapper to importlib for optional dependencies
    Updated 10/2023: use dask.delayed to read multiple files in parallel
    Updated 08/2023: use xarray h5netcdf to read files streaming from s3
        add open_dataset function for opening multiple granules
        add merging of datasets in preparation for Release-3 data
    Updated 07/2023: use logging instead of warnings for import attempts
    Written 11/2022
"""
from __future__ import annotations
import os
from IS2view.utilities import import_dependency

# attempt imports
rioxarray = import_dependency('rioxarray')
rioxarray.merge = import_dependency('rioxarray.merge')
dask = import_dependency('dask')
xr = import_dependency('xarray')

# set environmental variable for anonymous s3 access
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'

# default engine for xarray
_default_engine = dict(nc='h5netcdf', zarr='zarr')

def open_dataset(granule,
        group: str | None = None,
        format: str = 'nc',
        parallel: bool = True,
        **kwargs
    ):
    """
    Reads and optionally merges gridded ICESat-2 files

    Parameters
    ----------
    granule: str or list
        presigned url or path for granule(s) as a s3fs object
    group: str or NoneType, default None
        Data group to read
    format: str, default 'nc'
        Data format to read
    parallel: bool, default True
        Open files in parallel using ``dask.delayed``
    kwargs: dict
        Keyword arguments to pass to ``xarray`` reader

    Returns
    -------
    ds: object
        ``xarray`` dataset
    """
    # check if merging multiple granules
    if isinstance(granule, list):
        # merge multiple granules
        datasets = []
        closers = []
        if parallel:
            opener = dask.delayed(from_file)
            getattrs = dask.delayed(getattr)
        else:
            opener = from_file
            getattrs = getattr
        # read each granule and append to list
        for g in granule:
            datasets.append(opener(g,
                group=group,
                format=format,
                **kwargs)
            )
        closers = [getattrs(ds, "_close") for ds in datasets]
        # read datasets as dask arrays
        if parallel:
            datasets, closers = dask.compute(datasets, closers)
        # merge datasets
        ds = rioxarray.merge.merge_datasets(datasets)
    else:
        # read a single granule
        ds = from_file(granule,
            group=group,
            format=format,
            **kwargs
        )
    # return the dataset
    return ds

def from_file(granule,
        group: str | None = None,
        format: str = 'nc',
        **kwargs
    ):
    """
    Reads a gridded ICESat-2 file using ``rioxarray`` or ``xarray``

    Parameters
    ----------
    granule: str
        presigned url or path for granule
    group: str or NoneType, default None
        Data group to read
    format: str, default 'nc'
        Data format to read
    kwargs: dict
        Keyword arguments to pass to ``xarray`` reader

    Returns
    -------
    ds: object
        ``xarray`` dataset
    """
    # set default engine
    kwargs.setdefault('engine', _default_engine[format])
    if isinstance(granule, str) and format in ('nc',):
        ds = from_rasterio(granule,
            group=group,
            **kwargs
        )
    else:
        # read a single granule
        ds = from_xarray(granule,
            group=group,
            **kwargs
        )
    # return the dataset
    return ds

def from_rasterio(granule,
        group: str | None = None,
        **kwargs
    ):
    """
    Reads a gridded ICESat-2 file using ``rioxarray``

    Parameters
    ----------
    granule: str
        presigned url or path for granule
    group: str or NoneType, default None
        Data group to read
    kwargs: dict
        Keyword arguments to pass to ``rioxarray``

    Returns
    -------
    ds: object
        ``xarray`` dataset
    """
    ds = rioxarray.open_rasterio(granule,
        group=group,
        masked=True,
        **kwargs
    )
    return ds

def from_xarray(granule,
        group: str | None = None,
        engine: str = 'h5netcdf',
        **kwargs
    ):
    """
    Reads a gridded ICESat-2 file using ``xarray``

    Parameters
    ----------
    granule: str
        presigned url or path for granule
    group: str or NoneType, default None
        Data group to read
    engine: str, default 'h5netcdf'
        Engine to use when reading files
    kwargs: dict
        Keyword arguments to pass to ``xarray``

    Returns
    -------
    ds: object
        ``xarray`` dataset
    """
    kwargs.setdefault('variable', [])
    variable = kwargs.pop('variable')
    # read xarray dataset
    ds = xr.open_dataset(granule,
        group=group,
        engine=engine,
        chunks='auto',
        decode_cf=True,
        mask_and_scale=True,
        decode_times=False,
        concat_characters=True,
        decode_coords=True,
        overwrite_encoded_chunks=False,
        **kwargs
    )
    # set the coordinate reference system
    ds.rio.write_crs(ds.Polar_Stereographic.attrs['crs_wkt'], inplace=True)
    # reduce xarray dataset to specific variables
    if any(variable):
        ds = ds[variable]
    # flip orientation of y dimension
    ds = ds.isel(y=slice(None, None, -1))
    return ds
