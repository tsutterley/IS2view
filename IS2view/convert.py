"""
convert.py
Written by Tyler Sutterley (06/2024)
Utilities for converting gridded ICESat-2 files from native netCDF4

PYTHON DEPENDENCIES:
    h5netcdf: Pythonic interface to netCDF4 via h5py
        https://h5netcdf.org/
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    xarray: N-D labeled arrays and datasets in Python
        https://docs.xarray.dev/en/stable/

UPDATE HISTORY:
    Updated 06/2024: use wrapper to importlib for optional dependencies
    Updated 08/2023: use h5netcdf as the netCDF4 driver for xarray
    Updated 07/2023: use logging instead of warnings for import attempts
    Updated 06/2023: using pathlib to define and expand paths
    Updated 11/2022: output variables and attributes in top-level group
        use netCDF4 directly due to changes in xarray backends
    Written 07/2022
"""
import logging
import pathlib
import numpy as np
from IS2view.utilities import import_dependency

# attempt imports
h5netcdf = import_dependency('h5netcdf')
xr = import_dependency('xarray')

# default groups to skip
_default_skip_groups = ('METADATA', 'orbit_info', 'quality_assessment',)

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
            keyword arguments for output
        """
        kwds.setdefault('filename', self.filename)
        kwds.setdefault('output', self.output)
        kwds.setdefault('skip_groups', _default_skip_groups)
        # update filenames
        self.filename = kwds['filename']
        self.output = kwds['output']
        # split extension from netCDF4 file
        if isinstance(self.filename, (str, pathlib.Path)):
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
        with h5netcdf.File(self.filename) as source:
            # copy variables and attributes from the top-level group
            # copy everything from the netCDF4 file to the zarr file
            ds = xr.open_dataset(xr.backends.h5netcdf_.H5NetCDFStore(source))
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
                ds = xr.open_dataset(xr.backends.h5netcdf_.H5NetCDFStore(nc))
                ds.to_zarr(store=self.output, mode='a', group=group)
