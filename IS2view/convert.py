"""
convert.py
Written by Tyler Sutterley (07/2022)
Utilities for converting gridded ICESat-2 files into zarr files

PYTHON DEPENDENCIES:
    netCDF4: Python interface to the netCDF C library
        https://unidata.github.io/netcdf4-python/netCDF4/index.html
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    xarray: N-D labeled arrays and datasets in Python
        https://docs.xarray.dev/en/stable/

UPDATE HISTORY:
    Written 07/2022
"""
import os
import logging
import warnings
import numpy as np
# attempt imports
try:
    import xarray as xr
except (ImportError, ModuleNotFoundError) as e:
    warnings.filterwarnings("always")
    warnings.warn("xarray not available")
    warnings.warn("Some functions will throw an exception if called")
# ignore warnings
warnings.filterwarnings("ignore")

class convert():
    np.seterr(invalid='ignore')
    def __init__(self, filename=None, output=None):
        """Utilities for converting gridded ICESat-2 files into zarr files

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
            fileBasename,_ = os.path.splitext(self.filename)
        else:
            fileBasename,_ = os.path.splitext(self.filename.filename)
        # output zarr file
        if self.output is None:
            self.output = os.path.expanduser('{0}.zarr'.format(fileBasename))
        # log input and output files
        logging.info(self.filename)
        logging.info(self.output)
        # find each group within the input netCDF4 file
        with xr.backends.netCDF4_.netCDF4.Dataset(self.filename) as source:
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
