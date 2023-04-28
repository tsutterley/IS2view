"""
io.py
Written by Tyler Sutterley (11/2022)
Utilities for reading gridded ICESat-2 files using rasterio and xarray

PYTHON DEPENDENCIES:
    netCDF4: Python interface to the netCDF C library
        https://unidata.github.io/netcdf4-python/netCDF4/index.html
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
    Written 11/2022
"""
import os
import logging
import warnings
import numpy as np

# attempt imports
try:
    import rioxarray
except (ImportError, ModuleNotFoundError) as exc:
    warnings.filterwarnings("module")
    warnings.warn("rioxarray not available")
    warnings.warn("Some functions will throw an exception if called")
try:
    import xarray as xr
except (ImportError, ModuleNotFoundError) as exc:
    warnings.filterwarnings("module")
    warnings.warn("xarray not available")
    warnings.warn("Some functions will throw an exception if called")
# ignore warnings
warnings.filterwarnings("ignore")

# set environmental variable for anonymous s3 access
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'

def from_file(granule, group=None, format='nc', **kwargs):
    """
    Wrapper function for reading gridded ICESat-2 files

    Parameters
    ----------
    granule: str
        presigned url or path for granule
    group: str or NoneType, default None
        Data group to read
    format: str, default 'nc'
        Data format to read
    kwargs: dict
        Keyword arguments to pass to nc reader

    Returns
    -------
    ds: object
        xarray dataset
    """
    if format in ('nc',):
        return from_rasterio(granule, group=group, **kwargs)
    elif format in ('zarr',):
        return from_xarray(granule, group=group, engine=format, **kwargs)

def from_rasterio(granule, group=None, **kwargs):
    """
    Reads gridded ICESat-2 files using rioxarray

    Parameters
    ----------
    granule: str
        presigned url or path for granule
    group: str or NoneType, default None
        Data group to read
    kwargs: dict
        Keyword arguments to pass to rioxarray

    Returns
    -------
    ds: object
        xarray dataset
    """
    ds = rioxarray.open_rasterio(granule, group=group, masked=True, **kwargs)
    return ds

def from_xarray(granule, group=None, engine='zarr', **kwargs):
    """
    Reads gridded ICESat-2 files using xarray

    Parameters
    ----------
    granule: str
        presigned url or path for granule
    group: str or NoneType, default None
        Data group to read
    engine: str, default 'zarr'
        Engine to use when reading files
    kwargs: dict
        Keyword arguments to pass to xarray

    Returns
    -------
    ds: object
        xarray dataset
    """
    kwargs.setdefault('variable', [])
    variable = kwargs.pop('variable')
    # read xarray dataset
    ds = xr.open_dataset(granule, group=group, engine=engine,
        chunks='auto', decode_cf=True, mask_and_scale=True,
        decode_times=False, concat_characters=True, decode_coords=True,
        overwrite_encoded_chunks=False, **kwargs)
    # set the coordinate reference system
    ds.rio.write_crs(ds.Polar_Stereographic.attrs['crs_wkt'], inplace=True)
    # reduce xarray dataset to specific variables
    if any(variable):
        ds = ds[variable]
    # flip orientation of y dimension
    ds = ds.isel(y=slice(None, None, -1))
    return ds
