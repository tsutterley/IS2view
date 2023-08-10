"""
io.py
Written by Tyler Sutterley (08/2023)
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
    Updated 08/2023: use xarray h5netcdf to read files streaming from s3
        add merging of datasets in preparation for Release-3 data
    Updated 07/2023: use logging instead of warnings for import attempts
    Written 11/2022
"""
import os
import logging

# attempt imports
try:
    import rioxarray
    import rioxarray.merge
except (ImportError, ModuleNotFoundError) as exc:
    logging.critical("rioxarray not available")
try:
    import xarray as xr
except (ImportError, ModuleNotFoundError) as exc:
    logging.critical("xarray not available")

# set environmental variable for anonymous s3 access
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'

# default engine for xarray
_default_engine = dict(nc='h5netcdf', zarr='zarr')

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
        Keyword arguments to pass to xarray reader

    Returns
    -------
    ds: object
        xarray dataset
    """
    # set default engine
    kwargs.setdefault('engine', _default_engine[format])
    # check if merging multiple granules
    if isinstance(granule, list):
        # merge multiple granules
        datasets = []
        # for each granule
        for g in granule:
            # append to list
            datasets.append(from_xarray(g, group=group, **kwargs))
        # merge datasets
        ds = rioxarray.merge.merge_datasets(datasets)
    else:
        ds = from_xarray(granule, group=group, **kwargs)
    # return the dataset
    return ds

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
