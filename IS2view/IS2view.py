#!/usr/bin/env python
u"""
IS2view.py
Written by Tyler Sutterley (07/2022)
Jupyter notebook, user interface and plotting tools for visualizing
    rioxarray variables on leaflet maps

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    ipywidgets: interactive HTML widgets for Jupyter notebooks and IPython
        https://ipywidgets.readthedocs.io/en/latest/
    ipyleaflet: Jupyter / Leaflet bridge enabling interactive maps
        https://github.com/jupyter-widgets/ipyleaflet
    matplotlib: Python 2D plotting library
        http://matplotlib.org/
        https://github.com/matplotlib/matplotlib

UPDATE HISTORY:
    Written 07/2022
"""
import io
import copy
import base64
import asyncio
import logging
import warnings
import numpy as np
import collections.abc
import matplotlib
import matplotlib.cm as cm
import matplotlib.colorbar
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from traitlets import HasTraits, Float, observe

# attempt imports
try:
    import ipywidgets
except (ImportError, ModuleNotFoundError) as e:
    warnings.filterwarnings("always")
    warnings.warn("ipywidgets not available")
    warnings.warn("Some functions will throw an exception if called")
try:
    import ipyleaflet
except (ImportError, ModuleNotFoundError) as e:
    warnings.filterwarnings("always")
    warnings.warn("ipyleaflet not available")
    warnings.warn("Some functions will throw an exception if called")
try:
    import rasterio.warp
except (ImportError, ModuleNotFoundError) as e:
    warnings.filterwarnings("always")
    warnings.warn("rasterio not available")
    warnings.warn("Some functions will throw an exception if called")
try:
    import xarray as xr
except (ImportError, ModuleNotFoundError) as e:
    warnings.filterwarnings("always")
    warnings.warn("xarray not available")
    warnings.warn("Some functions will throw an exception if called")
# ignore warnings
warnings.filterwarnings("ignore")

class widgets:
    def __init__(self, **kwargs):
        # set default keyword options
        kwargs.setdefault('style', {})
        # set style
        self.style = copy.copy(kwargs['style'])

        # dropdown menu for setting ATL14/15 region
        region_list = ['AA','CN','CS','GL','IS','SV','RA']
        self.region = ipywidgets.Dropdown(
            options=region_list,
            description='Region:',
            description_tooltip=("Region: ATL14/15 region\n\t"
                "AA: Antarctica\n\t"
                "CN: Northern Canadian Archipelago\n\t"
                "CS: Southern Canadian Archipelago\n\t"
                "GL: Greenland\n\t"
                "IS: Iceland\n\t"
                "SV: Svalbard\n\t"
                "RA: Russian High Arctic"),
            disabled=False,
            style=self.style,
        )

        # dropdown menu for selecting group to read from file
        group_list = ['delta_h','dhdt_lag1','dhdt_lag4','dhdt_lag8']
        self.group = ipywidgets.Dropdown(
            options=group_list,
            description='Group:',
            description_tooltip="Group: ATL15 data group to read from file",
            disabled=False,
            style=self.style,
        )

        # dropdown menu for selecting variable to draw on map
        variable_list = ['delta_h','dhdt']
        self.variable = ipywidgets.Dropdown(
            options=variable_list,
            description='Variable:',
            description_tooltip="Variable: variable to display on leaflet map",
            disabled=False,
            style=self.style,
        )

        # dropdown menu for selecting time lag to draw on map
        self.timelag = ipywidgets.IntSlider(
            description='Lag:',
            description_tooltip="Lag: time lag to draw on leaflet map",
            disabled=False,
            style=self.style,
        )

        # Reverse the colormap
        self.dynamic = ipywidgets.Checkbox(
            value=False,
            description='Dynamic',
            description_tooltip=("Dynamic: Dynamically set normalization range"),
            disabled=False,
            style=self.style,
        )

        # watch widgets for changes
        self.group.observe(self.set_atl15_defaults)
        self.dynamic.observe(self.set_dynamic)
        self.variable.observe(self.set_lag_visibility)

        # slider for normalization range
        self.range = ipywidgets.FloatRangeSlider(
            min = -10,
            max = 10,
            value = [-5,5],
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
            'viridis','plasma','inferno','magma','cividis']
        self.cmaps_listed['Sequential'] = ['Greys','Purples',
            'Blues','Greens','Oranges','Reds','YlOrBr','YlOrRd',
            'OrRd','PuRd','RdPu','BuPu','GnBu','PuBu','YlGnBu',
            'PuBuGn','BuGn','YlGn']
        self.cmaps_listed['Sequential (2)'] = ['binary','gist_yarg',
            'gist_gray','gray','bone','pink','spring','summer',
            'autumn','winter','cool','Wistia','hot','afmhot',
            'gist_heat','copper']
        self.cmaps_listed['Diverging'] = ['PiYG','PRGn','BrBG',
            'PuOr','RdGy','RdBu','RdYlBu','RdYlGn','Spectral',
            'coolwarm', 'bwr','seismic']
        self.cmaps_listed['Cyclic'] = ['twilight',
            'twilight_shifted','hsv']
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
        centers['AA'] = (-90.0,0.0)
        centers['CN'] = (79.0,-85.0)
        centers['CS'] = (70.0,-73.0)
        centers['GL'] = (72.5,-45.0)
        centers['IS'] = (64.5,-18.5)
        centers['SV'] = (79.0,19.0)
        centers['RA'] = (79.0,78.0)
        return centers[self.region.value]

    @property
    def zoom(self):
        """return default zoom level for map based on region
        """
        zooms = {}
        zooms['AA'] = 1
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


    def set_atl14_defaults(self, *args, **kwargs):
        """sets the default widget parameters for ATL14 variables
        """
        self.dynamic.value = True

    def set_atl15_defaults(self, *args, **kwargs):
        """sets the default widget parameters for ATL15 variables
        """
        group = copy.copy(self.group.value)
        variables = {}
        variables['delta_h'] = 'delta_h'
        variables['dhdt_lag1'] = 'dhdt'
        variables['dhdt_lag4'] = 'dhdt'
        variables['dhdt_lag8'] = 'dhdt'
        self.variable.value = variables[group]

    def set_variables(self, ds):
        self.variable.options = sorted(ds.keys())

    def set_dynamic(self, *args, **kwargs):
        if self.dynamic.value:
            self.range.min = -100
            self.range.max = 100
            self.range.value = [np.nan,np.nan]
            self.range.layout.display = 'none'
        else:
            self.range.min = -10
            self.range.max = 10
            self.range.value = [-5,5]
            self.range.layout.display = 'inline-flex'

    def set_lags(self, ds):
        self.timelag.value = 1
        self.timelag.min = 1
        # try setting the max lag
        try:
            self.timelag.max = len(ds['time'])
        except Exception as e:
            self.timelag.max = 0

    def set_lag_visibility(self, sender):
        # check if setting an invariant variable
        if self.variable.value in ('cell_area','ice_mask'):
            self.timelag.layout.display = 'none'
        else:
            self.timelag.layout.display = 'inline-flex'

    @property
    def lag(self):
        return self.timelag.value - 1

projections = {}
projections['EPSG:3857'] = dict(name='EPSG3857',custom=False),
projections['EPSG:3413'] = dict(
    name='EPSG:3413',
    custom=True,
    proj4def="""+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 +x_0=0 +y_0=0
            +ellps=WGS84 +datum=WGS84 +units=m +no_defs""",
    origin=[-4194304, 4194304],
    resolutions=[
        16384.0,
        8192.0,
        4096.0,
        2048.0,
        1024.0,
        512.0,
        256.0
    ],
    bounds=[
        [-4194304, -4194304],
        [4194304, 4194304]
    ]
)
projections['EPSG:3031'] = dict(
    name='EPSG:3031',
    custom=True,
    proj4def="""+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1
        +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs""",
    origin=[-4194304, 4194304],
    resolutions=[
        16384.0,
        8192.0,
        4096.0,
        2048.0,
        1024.0,
        512.0,
        256.0
    ],
    bounds=[
        [-4194304, -4194304],
        [4194304, 4194304]
    ]
)

# draw ipyleaflet map
class leaflet:
    def __init__(self, projection, **kwargs):
        # set default keyword arguments
        kwargs.setdefault('map', None)
        kwargs.setdefault('attribution', False)
        kwargs.setdefault('zoom_control', False)
        kwargs.setdefault('scale_control', False)
        kwargs.setdefault('cursor_control', True)
        kwargs.setdefault('layer_control', True)
        kwargs.setdefault('center', (0,0))
        kwargs.setdefault('zoom', 1)
        # create basemap in projection
        if (projection == 'North'):
            self.map = ipyleaflet.Map(center=kwargs['center'],
                zoom=kwargs['zoom'], max_zoom=5,
                attribution_control=kwargs['attribution'],
                basemap=ipyleaflet.basemaps.NASAGIBS.BlueMarble3413,
                crs=projections['EPSG:3413'])
            self.crs = 'EPSG:3413'
        elif (projection == 'South'):
            self.map = ipyleaflet.Map(center=kwargs['center'],
                zoom=kwargs['zoom'], max_zoom=5,
                attribution_control=kwargs['attribution'],
                basemap=ipyleaflet.basemaps.NASAGIBS.BlueMarble3031,
                crs=projections['EPSG:3031'])
            self.crs = 'EPSG:3031'
        else:
            # use a predefined ipyleaflet map
            self.map = kwargs['map']
            self.crs = self.map.crs['name']
        # add control for layers
        if kwargs['layer_control']:
            self.layer_control = ipyleaflet.LayersControl(position='topleft')
            self.map.add(self.layer_control)
            self.layers = self.map.layers
        # add control for zoom
        if kwargs['zoom_control']:
            zoom_slider = ipywidgets.IntSlider(description='Zoom level:',
                min=self.map.min_zoom, max=self.map.max_zoom, value=self.map.zoom)
            ipywidgets.jslink((zoom_slider, 'value'), (self.map, 'zoom'))
            zoom_control = ipyleaflet.WidgetControl(widget=zoom_slider,
                position='topright')
            self.map.add(zoom_control)
        # add control for spatial scale bar
        if kwargs['scale_control']:
            scale_control = ipyleaflet.ScaleControl(position='topright')
            self.map.add(scale_control)
        # add control for cursor position
        if kwargs['cursor_control']:
            self.cursor = ipywidgets.Label()
            cursor_control = ipyleaflet.WidgetControl(widget=self.cursor,
                position='bottomleft')
            self.map.add(cursor_control)
            # keep track of cursor position
            self.map.on_interaction(self.handle_interaction)

    # handle cursor movements for label
    def handle_interaction(self, **kwargs):
        """callback for handling mouse motion and setting location label
        """
        if (kwargs.get('type') == 'mousemove'):
            lat,lon = kwargs.get('coordinates')
            lon = self.wrap_longitudes(lon)
            self.cursor.value = u"""Latitude: {d[0]:8.4f}\u00B0,
                Longitude: {d[1]:8.4f}\u00B0""".format(d=[lat,lon])

    # fix longitudes to be -180:180
    def wrap_longitudes(self, lon):
        phi = np.arctan2(np.sin(lon*np.pi/180.0),np.cos(lon*np.pi/180.0))
        # convert phi from radians to degrees
        return phi*180.0/np.pi

    def add(self, obj):
        """wrapper function for adding layers and controls to leaflet maps
        """
        if isinstance(obj, collections.abc.Iterable):
            for o in obj:
                try:
                    self.map.add(o)
                except ipyleaflet.LayerException as e:
                    logging.info(f"{o} already on map")
                    pass
        else:
            try:
                self.map.add(obj)
            except ipyleaflet.LayerException as e:
                logging.info(f"{obj} already on map")
                pass

    def remove(self, obj):
        """wrapper function for removing layers and controls to leaflet maps
        """
        if isinstance(obj, collections.abc.Iterable):
            for o in obj:
                try:
                    self.map.remove(o)
                except ipyleaflet.LayerException as e:
                    logging.info(f"{o} already removed from map")
                    pass
        else:
            try:
                self.map.remove(obj)
            except ipyleaflet.LayerException as e:
                logging.info(f"{obj} already removed from map")
                pass

@xr.register_dataset_accessor('leaflet')
class LeafletMap(HasTraits):
    """A xarray.DataArray extension for interactive map plotting, based on ipyleaflet
    """
    north = Float(90)
    east = Float(180)
    south = Float(-90)
    west = Float(-180)
    @observe('north', 'east', 'south', 'west')
    def boundary_change(self, change):
        # add image object to map
        if self.image is not None:
            # attempt to remove layer
            self.remove(self.image)
            # create new image service layer
            self.image = ipyleaflet.ImageService(
                name=self.variable,
                crs=self.crs,
                interactive=True,
                update_interval=100,
                endpoint='local')
        # add click handler for popups
        if self.enable_popups:
            self.image.on_click(self.handle_click)
        # set the image url
        self.set_image_url()
        self.add(self.image)

    def __init__(self, ds):
        self._ds = ds
        self._ds_selected = None
        # initialize data and colorbars
        self.image = None
        self.colorbar = None
        # initialize point for time series plot
        self.point = None
        self.popup = None

    # add imagery data to leaflet map
    def plot(self, m, **kwargs):
        """Creates image plots on leaflet maps

        Parameters
        ----------
        variable : str, xarray variable to plot
        lag : int, time lag to plot if 3-dimensional
        cmap : str, matplotlib colormap
        vmin : float, minimum value for normalization
        vmax : float, maximum value for normalization
        norm : obj, matplotlib color normalization object
        opacity : float, opacity of image plot
        enable_popups : bool, enable contextual popups
        colorbar : bool, show colorbar for rendered variable
        position : str, position of colorbar on leaflet map
        """
        kwargs.setdefault('variable', 'delta_h')
        kwargs.setdefault('lag', 0)
        kwargs.setdefault('cmap', 'viridis')
        kwargs.setdefault('vmin', None)
        kwargs.setdefault('vmax', None)
        kwargs.setdefault('norm', None)
        kwargs.setdefault('opacity', 1.0)
        kwargs.setdefault('enable_popups', False)
        kwargs.setdefault('colorbar', True)
        kwargs.setdefault('position', 'topright')
        # set map and map coordinate reference system
        self.map = m
        crs = m.crs['name']
        self.crs = projections[crs]
        (self.left, self.top), (self.right, self.bottom) = self.map.pixel_bounds
        # enable contextual popups
        self.enable_popups = bool(kwargs['enable_popups'])
        # reduce to variable and lag
        self.variable = copy.copy(kwargs['variable'])
        self.lag = int(kwargs['lag'])
        if (self._ds[self.variable].ndim == 3) and ('time' in self._ds[self.variable].dims):
            self._ds_selected = self._ds[self.variable].sel(time=self._ds.time[self.lag])
            self._time = 2018.0 + (self._ds.time)/365.25
        elif (self._ds[self.variable].ndim == 3) and ('band' in self._ds[self.variable].dims):
            self._ds_selected = np.squeeze(self._ds[self.variable])
        else:
            self._ds_selected = self._ds[self.variable]
        # set colorbar limits to 2-98 percentile
        # if not using a defined plot range
        clim = self._ds_selected.quantile((0.02, 0.98)).values
        if (kwargs['vmin'] is None) or np.isnan(kwargs['vmin']):
            vmin = clim[0]
        else:
            vmin = np.copy(kwargs['vmin'])
        if (kwargs['vmax'] is None) or np.isnan(kwargs['vmax']):
            vmax = clim[-1]
        else:
            vmax = np.copy(kwargs['vmax'])
        # create matplotlib normalization
        if kwargs['norm'] is None:
            self.norm = colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        else:
            self.norm = copy.copy(kwargs['norm'])
        # get colormap
        self.cmap = copy.copy(cm.get_cmap(kwargs['cmap']))
        # get opacity
        self.opacity = float(kwargs['opacity'])
        # wait for changes
        asyncio.ensure_future(self.async_wait_for_bounds())
        self.image = ipyleaflet.ImageService(
            name=self.variable,
            crs=self.crs,
            interactive=True,
            update_interval=100,
            endpoint='local')
        # add click handler for popups
        if self.enable_popups:
            self.image.on_click(self.handle_click)
        # set the image url
        self.set_image_url()
        # add image object to map
        self.add(self.image)
        # add colorbar
        if kwargs['colorbar']:
            self.add_colorbar(
                label=self.variable,
                cmap=self.cmap,
                opacity=self.opacity,
                norm=self.norm,
                position=kwargs['position']
            )

    def wait_for_change(self, widget, value):
        future = asyncio.Future()
        def get_value(change):
            future.set_result(change.new)
            widget.unobserve(get_value, value)
        widget.observe(get_value, value)
        return future

    async def async_wait_for_bounds(self):
        if len(self.map.bounds) == 0:
            await self.wait_for_change(self.map, 'bounds')
        # check that bounds are close
        while True:
            self.get_bounds()
            await self.wait_for_change(self.map, 'bounds')
            if np.isclose(self.bounds, self.map.bounds).all():
                break
        # will update map

    def add(self, obj):
        """wrapper function for adding layers and controls to leaflet maps
        """
        try:
            self.map.add(obj)
        except ipyleaflet.LayerException as e:
            logging.info(f"{obj} already on map")
            pass

    def remove(self, obj):
        """wrapper function for removing layers and controls to leaflet maps
        """
        try:
            self.map.remove(obj)
        except ipyleaflet.LayerException as e:
            logging.info(f"{obj} already removed from map")
            pass

    @property
    def z(self):
        """get the map zoom level
        """
        return int(self.map.zoom)

    @property
    def resolution(self):
        """get the map resolution for a given zoom level
        """
        return self.map.crs['resolutions'][self.z]

    def map_bounds(self):
        """get the bounds of the leaflet map in projected coordinates
        """
        # get SW and NE corners in map coordinates
        (self.left, self.top), (self.right, self.bottom) = self.map.pixel_bounds
        self.sw = dict(x=(self.map.crs['origin'][0] + self.left*self.resolution),
            y=(self.map.crs['origin'][1] - self.bottom*self.resolution))
        self.ne = dict(x=(self.map.crs['origin'][0] + self.right*self.resolution),
            y=(self.map.crs['origin'][1] - self.top*self.resolution))
        return self

    def get_bounds(self):
        """get the bounds of the leaflet map in geographical coordinates
        """
        self.map_bounds()
        lon,lat = rasterio.warp.transform(self.crs['name'], 'EPSG:4326',
            [self.sw['x'], self.ne['x']],
            [self.sw['y'], self.ne['y']])
        # calculate bounds in latitude/longitude
        self.north = np.max(lat)
        self.east = np.max(lon)
        self.south = np.min(lat)
        self.west = np.min(lon)
        self.bounds = ((self.south, self.west),(self.north, self.east))

    def clip_image(self, ds):
        """clip xarray image to bounds of leaflet map
        """
        self.map_bounds()
        # attempt to get the coordinate reference system of the dataset
        try:
            crs = self._ds.rio.crs
        except Exception as e:
            crs = self._ds.Polar_Stereographic.attrs['crs_wkt']
        # convert map bounds to coordinate reference system of image
        minx,miny,maxx,maxy = rasterio.warp.transform_bounds(self.crs['name'],
            crs, self.sw['x'], self.sw['y'], self.ne['x'], self.ne['y'])
        # pad input image to map bounds
        padded = ds.rio.pad_box(minx=minx, maxx=maxx, miny=miny, maxy=maxy)
        # get affine transform of padded image
        pad_transform = padded.rio.transform()
        north = int((maxy - pad_transform.f)//pad_transform.e)
        east = int((maxx - pad_transform.c)//pad_transform.a) + 1
        south = int((miny - pad_transform.f)//pad_transform.e) + 1
        west = int((minx - pad_transform.c)//pad_transform.a)
        # image extents
        self.extent = np.array([minx, maxx, miny, maxy])
        # clip image to map bounds
        return padded.isel(x=slice(west,east), y=slice(north,south))

    def get_image_url(self):
        """create the image url for the imageservice
        """
        fig, ax = plt.subplots(1, figsize=(15, 8))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        visible = self.clip_image(self._ds_selected)
        visible.plot.imshow(ax=ax,
            norm=self.norm,
            interpolation="nearest",
            cmap=self.cmap,
            alpha=self.opacity,
            add_colorbar=False,
            add_labels=False
        )
        # set image extent
        ax.set_xlim(self.extent[0], self.extent[1])
        ax.set_ylim(self.extent[2], self.extent[3])
        ax.axis("tight")
        ax.axis("off")
        # save as in-memory png
        png = io.BytesIO()
        plt.savefig(png, format='png')
        plt.close()
        png.seek(0)
        # encode to base64 and get url
        data = base64.b64encode(png.read()).decode("ascii")
        self.url = "data:image/png;base64," + data
        return self

    def set_image_url(self, *args, **kwargs):
        """set the url for the imageservice
        """
        self.get_bounds()
        self.get_image_url()
        self.image.url = self.url

    # functional calls for click events
    def handle_click(self, **kwargs):
        """callback for handling mouse clicks
        """
        lat,lon = kwargs.get('coordinates')
        kwargs.setdefault('color', 'red')
        kwargs.setdefault('width', 4.0)
        kwargs.setdefault('height', 3.0)
        # remove any prior instances of popup
        if self.popup is not None:
            self.remove(self.popup)
        # attempt to get the coordinate reference system of the dataset
        try:
            crs = self._ds.rio.crs
        except Exception as e:
            crs = self._ds.Polar_Stereographic.attrs['crs_wkt']
        # get the clicked point in dataset coordinate reference system
        x,y = rasterio.warp.transform('EPSG:4326', crs, [lon], [lat])
        # create figure or textual popup
        if (self._ds[self.variable].ndim == 3) and ('time' in self._ds[self.variable].dims):
            self.point = np.zeros_like(self._ds.time)
            self._time = 2018.0 + (self._ds.time)/365.25
            long_name = self._ds[self.variable].attrs['long_name'].replace('  ', ' ')
            self.units = self._ds[self.variable].attrs['units'][0]
            for i,t in enumerate(self._ds.time):
                self.point[i] = self._ds[self.variable].sel(x=x, y=y, time=t, method='nearest')
            # only create plot if valid
            if np.all(np.isnan(self.point)):
                return
            # create time series plot
            fig, ax = plt.subplots(figsize=(kwargs['width'], kwargs['height']))
            fig.patch.set_facecolor('white')
            ax.plot(self._time, self.point, color=kwargs['color'])
            ax.set_xlabel('{0} [{1}]'.format('time', 'years'))
            ax.set_ylabel('{0} [{1}]'.format(long_name, self.units))
            # save time series plot to in-memory png object
            png = io.BytesIO()
            plt.savefig(png, bbox_inches='tight', format='png')
            png.seek(0)
            plt.close()
            # create output widget
            child = ipywidgets.Image(value=png.getvalue(), format='png')
            self.popup = ipyleaflet.Popup(location=(lat,lon), child=child,
                min_width=300, max_width=300, min_height=300, max_height=300,
                name='popup')
            self.add(self.popup)
        elif (self._ds[self.variable].ndim == 3) and ('band' in self._ds[self.variable].dims):
            self.point = self._ds[self.variable].sel(x=x, y=y, band=0, method='nearest').data[0]
            self.units = self._ds[self.variable].attrs['units'][0]
            child = ipywidgets.HTML()
            child.value = '{0:0.1f} {1}'.format(np.squeeze(self.point), self.units)
            self.popup = ipyleaflet.Popup(location=(lat,lon), child=child, name='popup')
            self.add(self.popup)
        else:
            self.point = self._ds[self.variable].sel(x=x, y=y, method='nearest').data[0]
            self.units = self._ds[self.variable].attrs['units']
            child = ipywidgets.HTML()
            child.value = '{0:0.1f} {1}'.format(np.squeeze(self.point), self.units)
            self.popup = ipyleaflet.Popup(location=(lat,lon), child=child, name='popup')
            self.add(self.popup)

    # add colorbar widget to leaflet map
    def add_colorbar(self, **kwargs):
        """Creates colorbars on leaflet maps

        Parameters
        ----------
        cmap : str, matplotlib colormap
        norm : obj, matplotlib color normalization object
        opacity : float, opacity of colormap
        orientation : str, orientation of colorbar
        label : str, label for colorbar
        position : str, position of colorbar on leaflet map
        width : float, width of colorbar
        height : float, height of colorbar
        """
        kwargs.setdefault('cmap', 'viridis')
        kwargs.setdefault('norm', None)
        kwargs.setdefault('opacity', 1.0)
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('label', 'delta_h')
        kwargs.setdefault('position', 'topright')
        kwargs.setdefault('width', 6.0)
        kwargs.setdefault('height', 0.4)
        # remove any prior instances of a colorbar
        if self.colorbar is not None:
            self.remove(self.colorbar)
        # create matplotlib colorbar
        _, ax = plt.subplots(figsize=(kwargs['width'], kwargs['height']))
        cbar = matplotlib.colorbar.ColorbarBase(ax,
            cmap=kwargs['cmap'],
            norm=kwargs['norm'],
            alpha=kwargs['opacity'],
            orientation=kwargs['orientation'],
            label=kwargs['label'])
        cbar.solids.set_rasterized(True)
        cbar.ax.tick_params(which='both', width=1, direction='in')
        # save colorbar to in-memory png object
        png = io.BytesIO()
        plt.savefig(png, bbox_inches='tight', format='png')
        png.seek(0)
        # create output widget
        output = ipywidgets.Image(value=png.getvalue(), format='png')
        self.colorbar = ipyleaflet.WidgetControl(widget=output,
            transparent_bg=True, position=kwargs['position'])
        # add colorbar
        self.add(self.colorbar)
        plt.close()
