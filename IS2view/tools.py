#!/usr/bin/env python
u"""
tools.py
Written by Tyler Sutterley (11/2023)
User interface tools for Jupyter Notebooks

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    ipywidgets: interactive HTML widgets for Jupyter notebooks and IPython
        https://ipywidgets.readthedocs.io/en/latest/
    matplotlib: Python 2D plotting library
        http://matplotlib.org/
        https://github.com/matplotlib/matplotlib

UPDATE HISTORY:
    Updated 06/2024: use wrapper to importlib for optional dependencies
    Updated 11/2023: set time steps using decimal years rather than lags
        setting dynamic colormap with float64 min and max
    Updated 08/2023: added options for ATL14/15 Release-03 data
    Updated 07/2023: use logging instead of warnings for import attempts
    Updated 06/2023: moved widgets functions to separate module
    Updated 12/2022: added case for warping input image
    Updated 11/2022: modifications for dask-chunked rasters
    Written 07/2022
"""
import os
import copy
import logging
import numpy as np
from IS2view.utilities import import_dependency

# attempt imports
ipywidgets = import_dependency('ipywidgets')
cm = import_dependency('matplotlib.cm')

# set environmental variable for anonymous s3 access
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'

class widgets:
    def __init__(self, **kwargs):
        # set default keyword options
        kwargs.setdefault('loglevel', logging.CRITICAL)
        kwargs.setdefault('directory', os.getcwd())
        kwargs.setdefault('style', {})
        # set logging level
        logging.basicConfig(level=kwargs['loglevel'])
        # set style
        self.style = copy.copy(kwargs['style'])
        # pass through some ipywidgets objects
        self.HBox = ipywidgets.HBox
        self.VBox = ipywidgets.VBox

        # dropdown menu for setting asset
        asset_list = ['nsidc-https', 'nsidc-s3', 'atlas-s3', 'atlas-local']
        self.asset = ipywidgets.Dropdown(
            options=asset_list,
            value='nsidc-https',
            description='Asset:',
            description_tooltip=("Asset: Location to get the data\n\t"
                "nsidc-https: NSIDC on-prem DAAC\n\t"
                "nsidc-s3: NSIDC Cumulus s3 bucket`\n\t"
                "atlas-s3: s3 bucket in `us-west-2`\n\t"
                "atlas-local: local directory"),
            disabled=False,
            style=self.style,
        )

        # working data directory if local
        self.directory = ipywidgets.Text(
            value=kwargs['directory'],
            description='Directory:',
            description_tooltip=("Directory: working data directory"),
            disabled=False,
            style=self.style,
        )
        self.directory.layout.display = 'none'

        # dropdown menu for setting ATL14/15 release
        release_list = ['001', '002', '003', '004']
        self.release = ipywidgets.Dropdown(
            options=release_list,
            value='004',
            description='Release:',
            description_tooltip=("Release: ATL14/15 data release\n\t"
                "001: Release-01\n\t"
                "002: Release-02\n\t"
                "003: Release-03\n\t"
                "004: Release-04"),
            disabled=False,
            style=self.style,
        )

        # dropdown menu for setting ATL14/15 region
        # set as a default the release 03+ regions
        region_list = ['AA', 'A1', 'A2', 'A3', 'A4', 'CN', 'CS',
            'GL', 'IS', 'RA', 'SV']
        self.region = ipywidgets.Dropdown(
            options=region_list,
            description='Region:',
            description_tooltip=("Region: ATL14/15 region\n\t"
                "AA: Antarctica (merged)\n\t"
                "A1: Antarctica (0\u00B0 to 90\u00B0)\n\t"
                "A2: Antarctica (0\u00B0 to -90\u00B0)\n\t"
                "A3: Antarctica (-90\u00B0 to -180\u00B0)\n\t"
                "A4: Antarctica (90\u00B0 to 180\u00B0)\n\t"
                "CN: Northern Canadian Archipelago\n\t"
                "CS: Southern Canadian Archipelago\n\t"
                "GL: Greenland\n\t"
                "IS: Iceland\n\t"
                "SV: Svalbard\n\t"
                "RA: Russian High Arctic"),
            disabled=False,
            style=self.style,
        )

        # dropdown menu for setting ATL15 resolution
        resolution_list = ['01km', '10km', '20km', '40km']
        self.resolution = ipywidgets.Dropdown(
            options=resolution_list,
            description='Resolution:',
            description_tooltip=("Resolution: ATL15 resolution\n\t"
                "01km: 1 kilometer horizontal\n\t"
                "10km: 10 kilometers horizontal\n\t"
                "20km: 20 kilometers horizontal\n\t"
                "40km: 40 kilometers horizontal"),
            disabled=False,
            style=self.style,
        )

        # dropdown menu for selecting group to read from file
        # use Release-01 groups as the initial default
        group_list = ['delta_h', 'dhdt_lag1', 'dhdt_lag4', 'dhdt_lag8']
        self.group = ipywidgets.Dropdown(
            options=group_list,
            description='Group:',
            description_tooltip="Group: ATL15 data group to read from file",
            disabled=False,
            style=self.style,
        )

        # dropdown menu for selecting data format
        format_list = ['nc', 'zarr']
        self.format = ipywidgets.Dropdown(
            options=format_list,
            description='Format:',
            description_tooltip=("Format: ATL15 data format\n\t"
                "nc: Native netCDF4\n\t"
                "zarr: Cloud-optimized zarr"),
            disabled=False,
            style=self.style,
        )
        self.format.layout.display = 'none'

        # dropdown menu for selecting variable to draw on map
        variable_list = ['delta_h', 'dhdt']
        self.variable = ipywidgets.Dropdown(
            options=variable_list,
            description='Variable:',
            description_tooltip="Variable: variable to display on leaflet map",
            disabled=False,
            style=self.style,
        )

        # slider for selecting time lag to draw on map
        self.timelag = ipywidgets.IntSlider(
            description='Lag:',
            description_tooltip="Lag: time lag to draw on leaflet map",
            disabled=False,
            style=self.style,
        )

        # slider for selecting time step to draw on map
        self.timestep = ipywidgets.FloatSlider(
            description='Time:',
            description_tooltip="Time: time step to draw on leaflet map",
            step=0.25,
            readout=True,
            readout_format='.2f',
            disabled=False,
            continuous_update=False,
            style=self.style,
        )

        # Reverse the colormap
        self.dynamic = ipywidgets.Checkbox(
            value=False,
            description='Dynamic',
            description_tooltip="Dynamic: Dynamically set normalization range",
            disabled=False,
            style=self.style,
        )

        # watch widgets for changes
        self.asset.observe(self.set_directory_visibility)
        self.asset.observe(self.set_format_visibility)
        self.release.observe(self.set_groups)
        self.dynamic.observe(self.set_dynamic)
        self.variable.observe(self.set_time_visibility)
        self.timestep.observe(self.set_lag)

        # slider for normalization range
        self.range = ipywidgets.FloatRangeSlider(
            min = -10,
            max = 10,
            value = [-5, 5],
            description='Range:',
            description_tooltip=("Range: Plot normalization range"),
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            style=self.style,
        )

        # all listed colormaps in matplotlib version
        cmap_set = set(cm.datad.keys()) | set(cm.cmaps_listed.keys())
        # colormaps available in this program
        # (no reversed, qualitative or miscellaneous)
        self.cmaps_listed = {}
        self.cmaps_listed['Perceptually Uniform Sequential'] = [
            'viridis', 'plasma', 'inferno', 'magma', 'cividis']
        self.cmaps_listed['Sequential'] = ['Greys', 'Purples',
            'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd',
            'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu',
            'PuBuGn', 'BuGn', 'YlGn']
        self.cmaps_listed['Sequential (2)'] = ['binary', 'gist_yarg',
            'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer',
            'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot',
            'gist_heat', 'copper']
        self.cmaps_listed['Diverging'] = ['PiYG', 'PRGn', 'BrBG',
            'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral',
            'coolwarm', 'bwr', 'seismic']
        self.cmaps_listed['Cyclic'] = ['twilight',
            'twilight_shifted', 'hsv']
        # create list of available colormaps in program
        cmap_list = []
        for val in self.cmaps_listed.values():
            cmap_list.extend(val)
        # reduce colormaps to available in program and matplotlib
        cmap_set &= set(cmap_list)
        # dropdown menu for setting colormap
        self.cmap = ipywidgets.Dropdown(
            options=sorted(cmap_set),
            value='viridis',
            description='Colormap:',
            description_tooltip=("Colormap: matplotlib colormaps "
                "for displayed variable"),
            disabled=False,
            style=self.style,
        )

        # Reverse the colormap
        self.reverse = ipywidgets.Checkbox(
            value=False,
            description='Reverse Colormap',
            description_tooltip=("Reverse Colormap: reverse matplotlib "
                "colormap for displayed variable"),
            disabled=False,
            style=self.style,
        )

    @property
    def projection(self):
        """return string for map projection based on region
        """
        projections = {}
        projections['AA'] = 'South'
        projections['A1'] = 'South'
        projections['A2'] = 'South'
        projections['A3'] = 'South'
        projections['A4'] = 'South'
        projections['CN'] = 'North'
        projections['CS'] = 'North'
        projections['GL'] = 'North'
        projections['IS'] = 'North'
        projections['SV'] = 'North'
        projections['RA'] = 'North'
        return projections[self.region.value]

    @property
    def center(self):
        """return default central point latitude and longitude
        for map based on region
        """
        centers = {}
        centers['AA'] = (-90.0, 0.0)
        centers['A1'] = (-90.0, 0.0)
        centers['A2'] = (-90.0, 0.0)
        centers['A3'] = (-90.0, 0.0)
        centers['A4'] = (-90.0, 0.0)
        centers['CN'] = (79.0, -85.0)
        centers['CS'] = (70.0, -73.0)
        centers['GL'] = (72.5, -45.0)
        centers['IS'] = (64.5, -18.5)
        centers['SV'] = (79.0, 19.0)
        centers['RA'] = (79.0, 78.0)
        return centers[self.region.value]

    @property
    def zoom(self):
        """return default zoom level for map based on region
        """
        zooms = {}
        zooms['AA'] = 1
        zooms['A1'] = 1
        zooms['A2'] = 1
        zooms['A3'] = 1
        zooms['A4'] = 1
        zooms['CN'] = 2
        zooms['CS'] = 2
        zooms['GL'] = 1
        zooms['IS'] = 3
        zooms['SV'] = 3
        zooms['RA'] = 2
        return zooms[self.region.value]

    @property
    def _r(self):
        """return string for reversed Matplotlib colormaps
        """
        cmap_reverse_flag = '_r' if self.reverse.value else ''
        return cmap_reverse_flag

    @property
    def colormap(self):
        """return string for Matplotlib colormaps
        """
        return self.cmap.value + self._r

    @property
    def vmin(self):
        """return minimum of normalization range
        """
        return self.range.value[0]

    @property
    def vmax(self):
        """return maximum of normalization range
        """
        return self.range.value[1]

    def set_directory_visibility(self, sender):
        """updates the visibility of the directory widget
        """
        if (self.asset.value == 'atlas-local'):
            self.directory.layout.display = 'inline-flex'
        else:
            self.directory.layout.display = 'none'

    def set_format_visibility(self, sender):
        """updates the visibility of the data format widget
        """
        if self.asset.value in ('atlas-s3','atlas-local'):
            self.format.layout.display = 'inline-flex'
        else:
            self.format.layout.display = 'none'
            # set the format back to the default
            self.format.value = 'nc'

    def set_atl14_defaults(self, *args, **kwargs):
        """sets the default widget parameters for ATL14 variables
        """
        # use dynamic normalization
        self.dynamic.value = True

    def set_atl15_defaults(self, *args, **kwargs):
        """sets the default widget parameters for ATL15 variables
        """
        group = copy.copy(self.group.value)
        variables = {}
        variables['delta_h'] = 'delta_h'
        variables['dhdt_lag1'] = 'dhdt'
        # set annual time lags
        # extend possible time lags to 16 years post-launch
        for timelag in range(4, 68, 4):
            variables[f'dhdt_lag{timelag:d}'] = 'dhdt'
        # set default variable for group
        self.variable.value = variables[group]

    def set_groups(self, *args):
        """sets the list of available groups for a release
        """
        group_list = ['delta_h', 'dhdt_lag1', 'dhdt_lag4', 'dhdt_lag8']
        # append lag12 group
        if (int(self.release.value) > 1):
            group_list.append('dhdt_lag12')
        if (int(self.release.value) > 2):
            group_list.append('dhdt_lag16')
        # set group list
        self.group.options = group_list
        # change regions for Antarctica for Release-03+
        if (int(self.release.value) > 2):
            region_list = ['AA', 'A1', 'A2', 'A3', 'A4', 'CN', 'CS',
                'GL', 'IS', 'RA', 'SV']
            description_tooltip=("Region: ATL14/15 region\n\t"
                "AA: Antarctica (merged)\n\t"
                "A1: Antarctica (0\u00B0 to 90\u00B0)\n\t"
                "A2: Antarctica (0\u00B0 to -90\u00B0)\n\t"
                "A3: Antarctica (-90\u00B0 to -180\u00B0)\n\t"
                "A4: Antarctica (90\u00B0 to 180\u00B0)\n\t"
                "CN: Northern Canadian Archipelago\n\t"
                "CS: Southern Canadian Archipelago\n\t"
                "GL: Greenland\n\t"
                "IS: Iceland\n\t"
                "SV: Svalbard\n\t"
                "RA: Russian High Arctic")
        else:
            region_list = ['AA', 'CN', 'CS', 'GL', 'IS', 'RA', 'SV']
            description_tooltip=("Region: ATL14/15 region\n\t"
                "AA: Antarctica\n\t"
                "CN: Northern Canadian Archipelago\n\t"
                "CS: Southern Canadian Archipelago\n\t"
                "GL: Greenland\n\t"
                "IS: Iceland\n\t"
                "SV: Svalbard\n\t"
                "RA: Russian High Arctic")
        # set region list
        self.region.options = region_list
        self.region.description_tooltip = description_tooltip

    def set_variables(self, *args):
        """sets the list of available variables
        """
        if isinstance(self.data_vars, list):
            # set list of available variables
            self.variable.options = sorted(self.data_vars)
        else:
            # return to temporary defaults
            self.variable.options = ['delta_h', 'dhdt']

    def set_dynamic(self, *args, **kwargs):
        """sets variable normalization range if dynamic
        """
        if self.dynamic.value:
            fmin = np.finfo(np.float64).min
            fmax = np.finfo(np.float64).max
            self.range.min = fmin
            self.range.max = fmax
            self.range.value = [fmin, fmax]
            self.range.layout.display = 'none'
        else:
            self.range.min = -10
            self.range.max = 10
            self.range.value = [-5, 5]
            self.range.layout.display = 'inline-flex'

    def get_variables(self, d):
        """
        Gets the available variables and time steps
        
        Parameters
        ----------
        d : xarray.Dataset
            xarray.Dataset object
        """
        # data and time variables
        self.data_vars = sorted(d.data_vars)
        self.time_vars = d.time.values if 'time' in d else None
        # set the default groups
        self.set_groups()
        # set the default variables
        self.set_variables()
        # set the default time steps
        self.set_time_steps()
        
    def set_time_steps(self, *args, epoch=2018.0):
        """sets available time range
        """
        # try setting the min and max time step
        try:
            # convert time to units
            self.time = list(epoch + self.time_vars/365.25)
            self.timestep.max = self.time[-1]
            self.timestep.min = self.time[0]
            self.timestep.value = self.time[0]
        except Exception as exc:
            self.time = []
            self.timestep.max = 1
            self.timestep.min = 0
            self.timestep.value = 0

    def set_lag(self, sender):
        """sets available time range for lags
        """
        self.timelag.min = 1
        # try setting the max lag and value
        try:
            self.timelag.value = self.time.index(self.timestep.value) + 1
            self.timelag.max = len(self.time)
        except Exception as exc:
            self.timelag.value = 1
            self.timelag.max = 1

    def set_time_visibility(self, sender):
        """updates the visibility of the time widget
        """
        # list of invariant parameters
        invariant_parameters = ['ice_mask']
        if (int(self.release.value) <= 1):
            invariant_parameters.append('cell_area')
        # check if setting an invariant variable
        if self.variable.value in invariant_parameters:
            self.timestep.layout.display = 'none'
        else:
            self.timestep.layout.display = 'inline-flex'

    @property
    def lag(self):
        """return the 0-based index for the time lag
        """
        return self.timelag.value - 1
