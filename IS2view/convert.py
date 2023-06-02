"""
convert.py
Written by Tyler Sutterley (06/2023)
Utilities for converting gridded ICESat-2 files from native netCDF4

PYTHON DEPENDENCIES:
    netCDF4: Python interface to the netCDF C library
        https://unidata.github.io/netcdf4-python/netCDF4/index.html
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    xarray: N-D labeled arrays and datasets in Python
        https://docs.xarray.dev/en/stable/

UPDATE HISTORY:
    Updated 06/2023: using pathlib to define and expand paths
    Updated 11/2022: output variables and attributes in top-level group
        use netCDF4 directly due to changes in xarray backends
    Written 07/2022
"""
import logging
import pathlib
import warnings
import numpy as np

# attempt imports
try:
    import netCDF4
except (ImportError, ModuleNotFoundError) as exc:
    warnings.filterwarnings("module")
    warnings.warn("netCDF4 not available")
    warnings.warn("Some functions will throw an exception if called")
try:
    import xarray as xr
except (ImportError, ModuleNotFoundError) as exc:
    warnings.filterwarnings("module")
    warnings.warn("xarray not available")
    warnings.warn("Some functions will throw an exception if called")
# ignore warnings
warnings.filterwarnings("ignore")

class convert():
    np.seterr(invalid='ignore')
    def __init__(self, filename=None, output=None):
        """Utilities for converting gridded ICESat-2 files from native netCDF4

        Parameters
        ----------
        filename: str, obj or NoneType, default None
            input netCDF4 filename or io.BytesIO object
        """
        self.filename = filename
        self.output = output

    # PURPOSE: convert the netCDF4 file to zarr copying all file data
    def nc_to_zarr(self, **kwds):
        """
        convert a netCDF4 file to zarr copying all file data

        Parameters
        ----------
        **kwds: dict
            keyword arguments for output zarr converter
        """
        kwds.setdefault('filename', self.filename)
        kwds.setdefault('output', self.output)
        kwds.setdefault('skip_groups', ('METADATA',))
        # update filenames
        self.filename = kwds['filename']
        self.output = kwds['output']
        # split extension from netCDF4 file
        if isinstance(self.filename, str):
            filename = pathlib.Path(self.filename)
        else:
            filename = pathlib.Path(self.filename.filename)
        # output zarr file
        if self.output is None:
            self.output = filename.with_suffix('.zarr')
        # log input and output files
        logging.info(self.filename)
        logging.info(self.output)
        # find each group within the input netCDF4 file
        with netCDF4.Dataset(self.filename) as source:
            # copy variables and attributes from the top-level group
            # copy everything from the netCDF4 file to the zarr file
            ds = xr.open_dataset(xr.backends.NetCDF4DataStore(source))
            ds.to_zarr(store=self.output, mode='a')
            # for each group
            for group in source.groups.keys():
                # skip over specific groups
                if group in kwds['skip_groups']:
                    continue
                # get netCDF4 group
                logging.info(group)
                nc = source.groups.get(group)
                # copy everything from the netCDF4 group to the zarr file
                ds = xr.open_dataset(xr.backends.NetCDF4DataStore(nc))
                ds.to_zarr(store=self.output, mode='a', group=group)
