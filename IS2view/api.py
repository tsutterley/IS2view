#!/usr/bin/env python
u"""
api.py
Written by Tyler Sutterley (08/2023)
Plotting tools for visualizing rioxarray variables on leaflet maps

PYTHON DEPENDENCIES:
    geopandas: Python tools for geographic data
        http://geopandas.readthedocs.io/
    ipywidgets: interactive HTML widgets for Jupyter notebooks and IPython
        https://ipywidgets.readthedocs.io/en/latest/
    ipyleaflet: Jupyter / Leaflet bridge enabling interactive maps
        https://github.com/jupyter-widgets/ipyleaflet
    matplotlib: Python 2D plotting library
        http://matplotlib.org/
        https://github.com/matplotlib/matplotlib
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html
    OWSLib: Pythonic interface for Open Geospatial Consortium (OGC) web services
        https://owslib.readthedocs.io/
    rasterio: Access to geospatial raster data
        https://github.com/rasterio/rasterio
        https://rasterio.readthedocs.io
    xarray: N-D labeled arrays and datasets in Python
        https://docs.xarray.dev/en/stable/

UPDATE HISTORY:
    Updated 08/2023: add option for viewing full screen leaflet map
    Updated 07/2023: renamed module from IS2view.py to api.py
        add plot functions for map basemaps and added geometries
        add imshow function for visualizing current leaflet map
        use logging instead of warnings for import attempts
    Updated 06/2023: moved widgets functions to separate moddule
    Updated 12/2022: added case for warping input image
    Updated 11/2022: modifications for dask-chunked rasters
    Written 07/2022
"""
import io
import os
import copy
import json
import base64
import asyncio
import logging
import numpy as np
import collections.abc
from traitlets import HasTraits, Float, Tuple, observe
from traitlets.utils.bunch import Bunch

# attempt imports
try:
    import geopandas as gpd
except (AttributeError, ImportError, ModuleNotFoundError) as exc:
    logging.debug("geopandas not available")
try:
    import ipywidgets
except (AttributeError, ImportError, ModuleNotFoundError) as exc:
    logging.debug("ipywidgets not available")
try:
    import ipyleaflet
except (AttributeError, ImportError, ModuleNotFoundError) as exc:
    logging.debug("ipyleaflet not available")
try:
    import matplotlib
    import matplotlib.cm as cm
    import matplotlib.colorbar
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
except (AttributeError, ImportError, ModuleNotFoundError) as exc:
    logging.critical("matplotlib not available")
try:
    import owslib.wms
except (AttributeError, ImportError, ModuleNotFoundError) as exc:
    logging.debug("owslib not available")
try:
    import rasterio.transform
    import rasterio.warp
except (AttributeError, ImportError, ModuleNotFoundError) as exc:
    logging.critical("rasterio not available")
try:
    import xarray as xr
except (AttributeError, ImportError, ModuleNotFoundError) as exc:
    logging.critical("xarray not available")

# set environmental variable for anonymous s3 access
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'

# map projections
projections = {}
projections['EPSG:3857'] = dict(name='EPSG3857', custom=False),
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

# define optional background ipyleaflet image service layers
layers = Bunch()
try:
    # ArcticDEM
    layers.ArcticDEM = ipyleaflet.ImageService(
        name="ArcticDEM",
        attribution="""Esri, PGC, UMN, NSF, NGA, DigitalGlobe""",
        format='jpgpng',
        transparent=True,
        url='https://elevation2.arcgis.com/arcgis/rest/services/Polar/ArcticDEM/ImageServer',
        crs=projections['EPSG:3413']
    )
    # Reference Elevation Map of Antarctica (REMA)
    layers.REMA = ipyleaflet.ImageService(
        name="REMA",
        attribution="""Esri, PGC, UMN, NSF, NGA, DigitalGlobe""",
        format='jpgpng',
        transparent=True,
        url='https://elevation2.arcgis.com/arcgis/rest/services/Polar/AntarcticDEM/ImageServer',
        crs=projections['EPSG:3031']
    )
except (NameError, AttributeError):
    pass

# draw ipyleaflet map
class Leaflet:
    """Create interactive leaflet maps for visualizing ATL14/15 data

    Parameters
    ----------
    map : obj or NoneType, default None
        ``ipyleaflet.Map``
    attribution : bool, default False
        Include layer attributes on leaflet map
    scale_control : bool, default False
        Include spatial scale bar to map
    cursor_control : bool, default True
        Include display for cursor location
    full_screen_control: bool, default False
        Include control for full screen map view
    layer_control : bool, default True
        Include control for added map layers
    draw_control : bool, default False
        Include control for interactively drawing on map
    draw_tools : list, default ['marker', 'polyline', 'rectangle', 'polygon']
        Interactive drawing tools to include with control
    color : str, default 'blue'
        Color of drawn or included GeoJSON objects
    center : tuple, default (0, 0)
        Map center at (latitude, longitude)
    zoom : int, default 1
        Initial map zoom level

    Attributes
    ----------
    map : obj
        ``ipyleaflet.Map``
    crs : str
        Coordinate Reference System of map
    layer_control : obj
        ``ipyleaflet.LayersControl``
    scale_control : obj
        ``ipyleaflet.ScaleControl``
    cursor : obj
        ``ipywidgets.Label`` with cursor location
    geometries : dict
        GeoJSON formatted geometries
    """
    def __init__(self, projection, **kwargs):
        # set default keyword arguments
        kwargs.setdefault('map', None)
        kwargs.setdefault('attribution', False)
        kwargs.setdefault('full_screen_control', False)
        kwargs.setdefault('scale_control', False)
        kwargs.setdefault('cursor_control', True)
        kwargs.setdefault('layer_control', True)
        kwargs.setdefault('draw_control', False)
        default_draw_tools = ['marker', 'polyline', 'rectangle', 'polygon']
        kwargs.setdefault('draw_tools', default_draw_tools)
        kwargs.setdefault('color', 'blue')
        kwargs.setdefault('center', (0, 0))
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
        # add control for full screen
        if kwargs['full_screen_control']:
            self.full_screen_control = ipyleaflet.FullScreenControl()
            self.map.add(self.full_screen_control)
        # add control for layers
        if kwargs['layer_control']:
            self.layer_control = ipyleaflet.LayersControl(position='topleft')
            self.map.add(self.layer_control)
        # add control for spatial scale bar
        if kwargs['scale_control']:
            self.scale_control = ipyleaflet.ScaleControl(position='topright')
            self.map.add(self.scale_control)
        # add control for cursor position
        if kwargs['cursor_control']:
            self.cursor = ipywidgets.Label()
            cursor_control = ipyleaflet.WidgetControl(widget=self.cursor,
                position='bottomright')
            self.map.add(cursor_control)
            # keep track of cursor position
            self.map.on_interaction(self.handle_interaction)
        # add draw control
        if kwargs['draw_control']:
            # add control for drawing features on map
            draw_control = ipyleaflet.DrawControl(
                circlemarker={}, marker={}, polyline={},
                rectangle={}, polygon={}, edit=False)
            shapeOptions = {'color': kwargs['color'],
                'fill_color': kwargs['color']}
            # verify draw_tools is iterable
            if isinstance(kwargs['draw_tools'], str):
                kwargs['draw_tool'] = [kwargs['draw_tools']]
            # add marker tool
            if ('marker' in kwargs['draw_tools']):
                draw_control.marker = dict(
                    shapeOptions=shapeOptions
                )
            # add polyline tool
            if ('polyline' in kwargs['draw_tools']):
                draw_control.polyline = dict(
                    shapeOptions=shapeOptions
                )
            # add rectangle tool
            if ('rectangle' in kwargs['draw_tools']):
                draw_control.rectangle = dict(
                    shapeOptions=shapeOptions,
                    metric=['km', 'm']
                )
            # add polygon tool
            if ('polygon' in kwargs['draw_tools']):
                draw_control.polygon = dict(
                    shapeOptions=shapeOptions,
                    allowIntersection=False,
                    showArea=True,
                    metric=['km', 'm']
                )
            # geojson feature collection
            self.geometries = {}
            self.geometries['type'] = 'FeatureCollection'
            self.geometries['crs'] = 'epsg:4326'
            self.geometries['features'] = []
            # add control to map
            draw_control.on_draw(self.handle_draw)
            self.map.add(draw_control)

    # handle cursor movements for label
    def handle_interaction(self, **kwargs):
        """callback for handling mouse motion and setting location label
        """
        if (kwargs.get('type') == 'mousemove'):
            lat, lon = kwargs.get('coordinates')
            lon = self.wrap_longitudes(lon)
            self.cursor.value = u"""Latitude: {d[0]:8.4f}\u00B0,
                Longitude: {d[1]:8.4f}\u00B0""".format(d=[lat, lon])

    # keep track of objects drawn on map
    def handle_draw(self, obj, action, geo_json):
        """callback for handling draw events
        """
        # append geojson feature to list
        feature = copy.copy(geo_json)
        feature['properties'].pop('style')
        if (action == 'created'):
            self.geometries['features'].append(feature)
        elif (action == 'deleted'):
            self.geometries['features'].remove(feature)
        return self

    # fix longitudes to be -180:180
    def wrap_longitudes(self, lon):
        """Fix longitudes to be within -180 and 180
        """
        phi = np.arctan2(np.sin(lon*np.pi/180.0), np.cos(lon*np.pi/180.0))
        # convert phi from radians to degrees
        return phi*180.0/np.pi

    # add a geopandas GeoDataFrame to map and list of geometries
    def add_geodataframe(self, gdf, **kwargs):
        """Add a GeoDataFrame to map and append to list of geometries

        Parameters
        ----------
        gdf : obj
            geopandas GeoDataFrame
        kwargs : dict, default {}
            Keyword arguments for GeoJSON
        """
        # set default keyword arguments
        kwargs.setdefault('style', dict(color='blue'))
        # convert geodataframe to coordinate reference system
        # and to GeoJSON
        geodata = gdf.to_crs('epsg:4326').__geo_interface__
        geojson = ipyleaflet.GeoJSON(data=geodata, **kwargs)
        # add features to map
        self.map.add(geojson)
        # add geometries to list of features
        self.geometries['features'].extend(geodata['features'])
        return self

    # output geometries to GeoJSON
    def to_geojson(self, filename, **kwargs):
        """Output geometries to a GeoJSON file

        Parameters
        ----------
        filename : str
            Output GeoJSON filename
        kwargs : dict, default {}
            Additional attributes for the GeoJSON file
        """
        # dump the geometries to a geojson file
        kwargs.update(self.geometries)
        with open(filename, mode='w') as fid:
            json.dump(kwargs, fid)
        # print the filename and dictionary structure
        logging.info(filename)
        logging.info(list(kwargs.keys()))

    def add(self, obj):
        """wrapper function for adding layers and controls to leaflet maps
        """
        if isinstance(obj, collections.abc.Iterable):
            for o in obj:
                try:
                    self.map.add(o)
                except ipyleaflet.LayerException as exc:
                    logging.info(f"{o} already on map")
                    pass
                except ipyleaflet.ControlException as exc:
                    logging.info(f"{o} already on map")
                    pass
        else:
            try:
                self.map.add(obj)
            except ipyleaflet.LayerException as exc:
                logging.info(f"{obj} already on map")
                pass
            except ipyleaflet.ControlException as exc:
                logging.info(f"{obj} already on map")
                pass

    def remove(self, obj):
        """wrapper function for removing layers and controls to leaflet maps
        """
        if isinstance(obj, collections.abc.Iterable):
            for o in obj:
                try:
                    self.map.remove(o)
                except ipyleaflet.LayerException as exc:
                    logging.info(f"{o} already removed from map")
                    pass
                except ipyleaflet.ControlException as exc:
                    logging.info(f"{o} already removed from map")
                    pass
        else:
            try:
                self.map.remove(obj)
            except ipyleaflet.LayerException as exc:
                logging.info(f"{obj} already removed from map")
                pass
            except ipyleaflet.ControlException as exc:
                logging.info(f"{obj} already removed from map")
                pass

    # plot basemap
    def plot_basemap(self, ax=None, **kwargs):
        """Plot the current basemap

        Parameters
        ----------
        ax: obj, default None
            Figure axis
        kwargs: dict, default {}
            Additional keyword arguments for ``wms.getmap``
        """
        # set default keyword arguments
        kwargs.setdefault('layers', ['BlueMarble_NextGeneration'])
        kwargs.setdefault('format', 'image/png')
        kwargs.setdefault('srs', self.map.crs['name'])
        # create figure axis if non-existent
        if (ax is None):
            _, ax = plt.subplots()
        # get the pixel bounds and resolution of the map
        (left, top), (right, bottom) = self.map.pixel_bounds
        resolution = self.map.crs['resolutions'][int(self.map.zoom)]
        # calculate the size of the map in pixels
        kwargs.setdefault('size', [int((right-left)), int((bottom-top))])
        # calculate the bounding box of the map in projected coordinates
        bbox = [None]*4
        bbox[0] = self.map.crs['origin'][0] + left*resolution
        bbox[1] = self.map.crs['origin'][1] - bottom*resolution
        bbox[2] = self.map.crs['origin'][0] + right*resolution
        bbox[3] = self.map.crs['origin'][1] - top*resolution
        kwargs.setdefault('bbox', bbox)
        # create WMS request for basemap image at bounds and resolution
        srs = kwargs['srs'].replace(':', '').lower()
        # url of NASA Global Imagery Browse Services (GIBS)
        # https://wiki.earthdata.nasa.gov/display/GIBS
        # https://worldview.earthdata.nasa.gov/
        url = f'https://gibs.earthdata.nasa.gov/wms/{srs}/best/wms.cgi?'
        wms = owslib.wms.WebMapService(url=url, version='1.1.1')
        basemap = wms.getmap(**kwargs)
        # read WMS layer and plot
        img = plt.imread(io.BytesIO(basemap.read()))
        ax.imshow(img, extent=[bbox[0],bbox[2],bbox[1],bbox[3]])

    # plot geometries
    def plot_geometries(self, ax=None, **kwargs):
        """Plot the current geometries in the coordinate reference
        system (``crs``) of the map

        Parameters
        ----------
        ax: obj, default None
            Figure axis
        kwargs: dict, default {}
            Additional keyword arguments for ``plot``
        """
        # return if no geometries
        if (len(self.geometries['features']) == 0):
            return
        # create figure axis if non-existent
        if (ax is None):
            _, ax = plt.subplots()
        # create a geopandas GeoDataFrame from the geometries
        # convert coordinate reference system to map crs
        gdf = gpd.GeoDataFrame.from_features(self.geometries,
            crs=self.geometries['crs']).to_crs(self.crs)
        # create plot with all geometries
        gdf.plot(ax=ax, **kwargs)

    @property
    def layers(self):
        """get the map layers
        """
        return self.map.layers

    @property
    def controls(self):
        """get the map controls
        """
        return self.map.controls

# function for setting image service layers with raster functions
def image_service_layer(name, raster='hillshade'):
    """
    Creates image service layers with optional raster functions

    Parameters
    ----------
    name : str
        Name of the image service layer

            - ``ArcticDEM``
            - ``REMA``
    raster : str, default 'hillshade'
        Name of the raster function for image service layer

            - ``aspect``: Slope Aspect Map
            - ``contour``: Elevation Contours Map
            - ``ellipsoidal``: Ellipsoidal Elevation Map
            - ``hillshade``: Gray Hillshade Map
            - ``orthometric``: Orthometric Elevation Map
            - ``slope``: Slope Map
            - ``smoothed``: Smoothed Contours Map
            - ``tinted``: Tinted Hillshade Map
    """
    # available raster functions for each DEM
    if (name == 'ArcticDEM'):
        mapping = dict(
            aspect="Aspect Map",
            contour="Contour 25",
            ellipsoidal="Height Ellipsoidal",
            hillshade="Hillshade Gray",
            orthometric="Height Orthometric",
            slope="Slope Map",
            smoothed="Contour Smoothed 25",
            tinted="Hillshade Elevation Tinted"
        )
    elif (name == 'REMA'):
        mapping = dict(
            aspect="Aspect Map",
            contour="Contour 25",
            hillshade="Hillshade Gray",
            orthometric="Height Orthometric",
            slope="Slope Degrees Map",
            smoothed="Smooth Contour 25",
            tinted="Hillshade Elevation Tinted"
        )
    else:
        raise ValueError(f'Unknown image service layer {name}')
    # check if raster function is known layer
    if raster not in mapping.keys():
        raise ValueError(f'Unknown raster function {raster}')
    # add rendering rule to layer
    layer = copy.copy(layers[name])
    layer.rendering_rule = {"rasterFunction": mapping[raster]}
    return layer

@xr.register_dataset_accessor('leaflet')
class LeafletMap(HasTraits):
    """A xarray.DataArray extension for interactive map plotting, based on ipyleaflet

    Parameters
    ----------
    ds : obj
        ``xarray.Dataset``

    Attributes
    ----------
    _ds : obj
        ``xarray.Dataset``
    _ds_selected : obj
        ``xarray.Dataset`` for selected variable
    _variable : str
        Selected variable
    map : obj
        ``ipyleaflet.Map``
    crs : str
        Coordinate Reference System of map
    left, top, right, bottom : float
        Map bounds in image coordinates
    sw : dict
        Location of lower-left corner in projected coordinates
    ne : dict
        Location of upper-right corner in projected coordinates
    bounds : tuple
        Location of map bounds in geographical coordinates
    image : obj
        ``ipyleaflet.ImageService`` layer for variable
    cmap : obj
        Matplotlib colormap object
    norm : obj
        Matplotlib normalization object
    opacity : float
        Transparency of image service layer
    colorbar : obj
        ``ipyleaflet.WidgetControl`` with Matplotlib colorbar
    popup : obj
        ``ipyleaflet.Popup`` with value at clicked location
    _data : float
        Variable value at clicked location
    _units : str
        Units of selected variable
    """

    bounds = Tuple(Tuple(Float(), Float()), Tuple(Float(), Float()))
    @observe('bounds')
    def boundary_change(self, change):
        """Update image on boundary change
        """
        # add image object to map
        if self.image is not None:
            # attempt to remove layer
            self.remove(self.image)
            # create new image service layer
            self.image = ipyleaflet.ImageService(
                name=self._variable,
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
        # initialize map
        self.map = None
        self.crs = None
        self.left, self.top = (None, None)
        self.right, self.bottom = (None, None)
        self.sw = {}
        self.ne = {}
        # initialize dataset
        self._ds = ds
        self._ds_selected = None
        self._variable = None
        # initialize image and colorbars
        self.image = None
        self.cmap = None
        self.norm = None
        self.opacity = None
        self.colorbar = None
        # initialize attributes for popup
        self.enable_popups = False
        self.popup = None
        self._data = None
        self._units = None

    # add imagery data to leaflet map
    def plot(self, m, **kwargs):
        """Creates image plots on leaflet maps

        Parameters
        ----------
        m : obj
            leaflet map to add the layer
        variable : str, default 'delta_h'
            xarray variable to plot
        lag : int, default 0
            Time lag to plot if 3-dimensional
        cmap : str, default 'viridis'
            matplotlib colormap
        vmin : float or NoneType
            Minimum value for normalization
        vmax : float or NoneType
            Maximum value for normalization
        norm : obj or NoneType
            Matplotlib color normalization object
        opacity : float, default 1.0
            Opacity of image plot
        enable_popups : bool, default False
            Enable contextual popups
        colorbar : bool, decault True
            Show colorbar for rendered variable
        position : str, default 'topright'
            Position of colorbar on leaflet map
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
        self._variable = copy.copy(kwargs['variable'])
        self.lag = int(kwargs['lag'])
        if (self._ds[self._variable].ndim == 3) and ('time' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable].sel(time=self._ds.time[self.lag])
        elif (self._ds[self._variable].ndim == 3) and ('band' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable].sel(band=1)
        else:
            self._ds_selected = self._ds[self._variable]
        # set colorbar limits to 2-98 percentile
        # if not using a defined plot range
        clim = self._ds_selected.chunk(dict(y=-1,x=-1)).quantile((0.02, 0.98)).values
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
            name=self._variable,
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
                label=self._variable,
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
        except ipyleaflet.LayerException as exc:
            logging.info(f"{obj} already on map")
            pass
        except ipyleaflet.ControlException as exc:
            logging.info(f"{obj} already on map")
            pass

    def remove(self, obj):
        """wrapper function for removing layers and controls to leaflet maps
        """
        try:
            self.map.remove(obj)
        except ipyleaflet.LayerException as exc:
            logging.info(f"{obj} already removed from map")
            pass
        except ipyleaflet.ControlException as exc:
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

    def reset(self):
        """remove features from leaflet map
        """
        for layer in self.map.layers:
            if (layer._model_name == 'LeafletImageServiceModel') and \
                (layer.endpoint == 'local'):
                self.remove(layer)
            elif (layer._model_name == 'LeafletPopupModel'):
                self.remove(layer)
        for control in self.map.controls:
            if (control._model_name == 'LeafletWidgetControlModel') and \
                (control.widget._model_name == 'ImageModel'):
                self.remove(control)
        # reset layers and controls
        self.image = None
        self.popup = None
        self.colorbar = None

    # get map bounding box in projected coordinates
    def get_bbox(self):
        """get the bounding box of the leaflet map in projected coordinates
        """
        # get SW and NE corners in map coordinates
        (self.left, self.top), (self.right, self.bottom) = self.map.pixel_bounds
        self.sw = dict(x=(self.map.crs['origin'][0] + self.left*self.resolution),
            y=(self.map.crs['origin'][1] - self.bottom*self.resolution))
        self.ne = dict(x=(self.map.crs['origin'][0] + self.right*self.resolution),
            y=(self.map.crs['origin'][1] - self.top*self.resolution))
        return self

    # get map bounds in geographic coordinates
    def get_bounds(self):
        """get the bounds of the leaflet map in geographical coordinates
        """
        self.get_bbox()
        lon, lat = rasterio.warp.transform(
            self.crs['name'], 'EPSG:4326',
            [self.sw['x'], self.ne['x']],
            [self.sw['y'], self.ne['y']])
        # calculate bounds in latitude/longitude
        north = np.max(lat)
        east = np.max(lon)
        south = np.min(lat)
        west = np.min(lon)
        # update bounds
        self.bounds = ((south, west), (north, east))

    def get_crs(self):
        """Attempt to get the coordinate reference system of the dataset
        """
        # get coordinate reference system from grid mapping
        try:
            grid_mapping = self._ds[self._variable].attrs['grid_mapping']
            ds_crs = self._ds[grid_mapping].attrs['crs_wkt']
        except Exception as exc:
            pass
        else:
            self._ds.rio.set_crs(ds_crs)
            return
        # get coordinate reference system from crs attribute
        try:
            ds_crs = self._ds.rio.crs.to_wkt()
        except Exception as exc:
            pass
        else:
            self._ds.rio.set_crs(ds_crs)
            return
        # raise exception
        raise Exception('Unknown coordinate reference system')

    def clip_image(self, ds):
        """clip or warp xarray image to bounds of leaflet map
        """
        self.get_bbox()
        # attempt to get the coordinate reference system of the dataset
        self.get_crs()
        # convert map bounds to coordinate reference system of image
        minx, miny, maxx, maxy = rasterio.warp.transform_bounds(
            self.crs['name'], self._ds.rio.crs,
            self.sw['x'], self.sw['y'],
            self.ne['x'], self.ne['y'])
        # extent of the leaflet map
        self.extent = np.array([minx, maxx, miny, maxy])
        # compare data resolution and leaflet map resolution
        resolution = np.abs(ds.x[1] - ds.x[0]).values
        if (resolution > self.resolution):
            # pad input image to map bounds
            padded = ds.rio.pad_box(minx=minx, maxx=maxx, miny=miny, maxy=maxy)
            # get affine transform of padded image
            pad_transform = padded.rio.transform()
            north = int((maxy - pad_transform.f)//pad_transform.e)
            east = int((maxx - pad_transform.c)//pad_transform.a) + 1
            south = int((miny - pad_transform.f)//pad_transform.e) + 1
            west = int((minx - pad_transform.c)//pad_transform.a)
            # clip image to map bounds
            return padded.isel(x=slice(west, east), y=slice(north, south))
        else:
            # warp image to map bounds and resolution
            # input and output affine transformations
            src_transform = ds.rio.transform()
            dst_transform = rasterio.transform.from_origin(minx, maxy,
                self.resolution, self.resolution)
            # allocate for output warped image
            dst_width = int((maxx - minx)//self.resolution)
            dst_height = int((maxy - miny)//self.resolution)
            dst_data = np.zeros((dst_height, dst_width), dtype=ds.dtype.type)
            # warp image to output resolution
            rasterio.warp.reproject(source=ds.values, destination=dst_data,
                src_transform=src_transform,
                src_crs=self._ds.rio.crs,
                src_nodata=np.nan,
                dst_transform=dst_transform,
                dst_crs=self.crs['name'],
                dst_resolution=(self.resolution, self.resolution))
            # calculate centered coordinates
            transform = dst_transform * dst_transform.translation(0.5, 0.5)
            x_coords, _ = transform * (np.arange(dst_width), np.zeros(dst_width))
            _, y_coords = transform * (np.zeros(dst_height), np.arange(dst_height))
            # return DataAarray with warped image
            return xr.DataArray(
                name=ds.name,
                data=dst_data,
                coords=dict(y=y_coords, x=x_coords),
                dims=copy.deepcopy(ds.dims),
                attrs=copy.deepcopy(ds.attrs),
            )

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
        plt.savefig(png, format='png', transparent=True)
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

    def set_lag(self, sender):
        """update the time lag for the selected variable
        """
        # only update lag if a new final
        if isinstance(sender['new'], int):
            self.lag = sender['new'] - 1
        else:
            return
        # try to update the selected dataset
        try:
            self._ds_selected = self._ds[self._variable].sel(time=self._ds.time[self.lag])
            self.get_image_url()
        except Exception as exc:
            pass
        else:
            # update image url
            self.image.url = self.url
            # force redrawing of map by removing and adding layer
            self.remove(self.image)
            self.add(self.image)

    # functional calls for click events
    def handle_click(self, **kwargs):
        """callback for handling mouse clicks
        """
        lat, lon = kwargs.get('coordinates')
        # remove any prior instances of popup
        if self.popup is not None:
            self.remove(self.popup)
        # attempt to get the coordinate reference system of the dataset
        try:
            grid_mapping = self._ds[self._variable].attrs['grid_mapping']
            crs = self._ds[grid_mapping].attrs['crs_wkt']
        except Exception as exc:
            crs = self._ds.rio.crs.to_wkt()
        else:
            self._ds.rio.set_crs(crs)
        # get the clicked point in dataset coordinate reference system
        x, y = rasterio.warp.transform('EPSG:4326', crs, [lon], [lat])
        # find nearest point in dataset
        self._data = self._ds_selected.sel(x=x, y=y, method='nearest').values[0]
        self._units = self._ds[self._variable].attrs['units']
        # only create popup if valid
        if np.isnan(self._data):
            return
        # create contextual popup
        child = ipywidgets.HTML()
        child.value = '{0:0.1f} {1}'.format(np.squeeze(self._data), self._units)
        self.popup = ipyleaflet.Popup(location=(lat, lon),
            child=child, name='popup')
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
        plt.savefig(png, bbox_inches='tight', format='png', transparent=True)
        png.seek(0)
        # create output widget
        output = ipywidgets.Image(value=png.getvalue(), format='png')
        self.colorbar = ipyleaflet.WidgetControl(widget=output,
            transparent_bg=True, position=kwargs['position'])
        # add colorbar
        self.add(self.colorbar)
        plt.close()

    # save the current map as an image
    def imshow(self, ax=None, **kwargs):
        """Save the current map as a static image

        Parameters
        ----------
        ax: obj, default None
            Figure axis
        kwargs: dict, default {}
            Additional keyword arguments for ``imshow``
        """
        # create figure axis if non-existent
        if (ax is None):
            _, ax = plt.subplots()
        # extract units
        longname = self._ds[self._variable].attrs['long_name'].replace('  ', ' ')
        units = self._ds[self._variable].attrs['units'][0]
        # clip image to map bounds
        visible = self.clip_image(self._ds_selected)
        # color bar keywords
        cbar_kwargs = dict(label=f'{longname} [{units}]', orientation='horizontal')
        visible.plot.imshow(ax=ax,
            norm=self.norm,
            interpolation="nearest",
            cmap=self.cmap,
            alpha=self.opacity,
            add_colorbar=True,
            add_labels=True,
            cbar_kwargs=cbar_kwargs,
            **kwargs
        )
        # set image extent
        ax.set_xlim(self.extent[0], self.extent[1])
        ax.set_ylim(self.extent[2], self.extent[3])
        ax.set_aspect('equal', adjustable='box')

@xr.register_dataset_accessor('timeseries')
class TimeSeries(HasTraits):
    """A xarray.DataArray extension for extracting and plotting a time series

    Parameters
    ----------
    ds : obj
        ``xarray.Dataset``

    Attributes
    ----------
    _ds : obj
        ``xarray.Dataset``
    _ds_selected : obj
        ``xarray.Dataset`` for selected variable
    _variable : str
        Selected variable
    geometry : dict
        GeoJSON geometry of feature
    properties : dict
        GeoJSON properties of feature
    crs : str
        Coordinate Reference System of feature
    _data : float
        Variable value at geometry
    _area : float
        Area of geometry (``Polygon``, ``MultiPolygon``)
    _dist : str
        Eulerian distance from first point (``LineString``)
    _time : str
        Time coordinates in decimal-years
    _units : str
        Units of selected variable
    _longname : str
        Unit longname of selected variable
    _line : str
        Matplotlib line object from plot
    """

    def __init__(self, ds):
        # initialize feature
        self.geometry = {}
        self.properties = {}
        self.crs = None
        # initialize dataset
        self._ds = ds
        self._ds_selected = None
        self._variable = None
        # initialize data for time series plot
        self._data = None
        self._area = None
        self._dist = None
        self._time = None
        self._units = None
        self._longname = None
        self._line = None

    # create time series plot for a region
    def plot(self, feature,
        variable='delta_h',
        crs='epsg:4326',
        epoch=2018.0,
        ax=None,
        figsize=(6, 4),
        **kwargs
        ):
        """Plot a time series for an extracted geometry

        Parameters
        ----------
        feature : obj
            GeoJSON feature to extract
        variable : str, default 'delta_h'
            xarray variable to plot
        crs : str, default 'epsg:4326'
            coordinate reference system of geometry
        epoch : float, default 2018.0
            Reference epoch for delta times
        ax : obj or NoneType, default None
            Figure axis on which to plot

            Mutually exclusive with ``figsize``
        figsize : tuple, default (6,4)
            Dimensions of figure to create
        kwargs : dict, default {}
            Keyword arguments for time series plot
        """
        # set geometry
        self.geometry = feature.get('geometry') or {}
        # set properties with all keys lowercase
        properties = feature.get('properties') or {}
        self.properties = {k.lower(): v for k, v in properties.items()}
        # get coordinate reference system of geometry
        self.crs = crs
        # attempt to get the coordinate reference system of the dataset
        self.get_crs()
        # set figure axis
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
            fig.patch.set_facecolor('white')
        # reduce to variable
        self._variable = copy.copy(variable)
        if (self._ds[self._variable].ndim == 3) and ('time' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable]
        else:
            return
        # convert time to units
        self._time = epoch + (self._ds.time)/365.25
        # extract units
        self._longname = self._ds[self._variable].attrs['long_name'].replace('  ', ' ')
        self._units = self._ds[self._variable].attrs['units'][0]
        # create plot for a given geometry type
        geometry_type = self.geometry.get('type')
        if (geometry_type.lower() == 'point'):
            self.point(ax, **kwargs)
        elif (geometry_type.lower() == 'linestring'):
            self.transect(ax, **kwargs)
        elif geometry_type.lower() in ('polygon', 'multipolygon'):
            self.average(ax, **kwargs)
        else:
            raise ValueError(f'Invalid geometry type {geometry_type}')
        # return the class object
        return self

    # extract a time series plot for a region
    def extract(self, feature,
        variable='delta_h',
        crs='epsg:4326',
        epoch=2018.0,
        ):
        """Extract a time series for a geometry

        Parameters
        ----------
        feature : obj
            GeoJSON feature to extract
        variable : str, default 'delta_h'
            xarray variable to extract
        crs : str, default 'epsg:4326'
            coordinate reference system of geometry
        epoch : float, default 2018.0
            Reference epoch for delta times
        """
        # set geometry
        self.geometry = feature.get('geometry') or {}
        # set properties with all keys lowercase
        properties = feature.get('properties') or {}
        self.properties = {k.lower(): v for k, v in properties.items()}
        # get coordinate reference system of geometry
        self.crs = crs
        # attempt to get the coordinate reference system of the dataset
        self.get_crs()
        # reduce to variable
        self._variable = copy.copy(variable)
        if (self._ds[self._variable].ndim == 3) and ('time' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable]
        else:
            return
        # convert time to units
        self._time = epoch + (self._ds.time)/365.25
        # extract units
        self._longname = self._ds[self._variable].attrs['long_name'].replace('  ', ' ')
        self._units = self._ds[self._variable].attrs['units'][0]
        # create plot for a given geometry type
        geometry_type = self.geometry.get('type')
        if (geometry_type.lower() == 'point'):
            self.point(None)
        elif (geometry_type.lower() == 'linestring'):
            self.transect(None)
        elif geometry_type.lower() in ('polygon', 'multipolygon'):
            self.average(None)
        else:
            raise ValueError(f'Invalid geometry type {geometry_type}')
        # return the class object
        return self

    def get_crs(self):
        """Attempt to get the coordinate reference system of the dataset
        """
        # get coordinate reference system from grid mapping
        try:
            grid_mapping = self._ds[self._variable].attrs['grid_mapping']
            ds_crs = self._ds[grid_mapping].attrs['crs_wkt']
        except Exception as exc:
            pass
        else:
            self._ds.rio.set_crs(ds_crs)
            return
        # get coordinate reference system from crs attribute
        try:
            ds_crs = self._ds.rio.crs.to_wkt()
        except Exception as exc:
            pass
        else:
            self._ds.rio.set_crs(ds_crs)
            return
        # raise exception
        raise Exception('Unknown coordinate reference system')

    def point(self, ax, **kwargs):
        """Extracts and plots a time series for a geolocation

        Parameters
        ----------
        ax : obj or NoneType
            Figure axis on which to plot

            Will only extract time series if ``None``
        legend : bool, default False
            Add legend
        """
        # convert point to dataset coordinate reference system
        lon, lat = self.geometry['coordinates']
        x, y = rasterio.warp.transform(self.crs, self._ds.rio.crs, [lon], [lat])
        # output time series for point
        self._data = np.zeros_like(self._ds.time)
        # reduce dataset to geometry
        for i, t in enumerate(self._ds.time):
            self._data[i] = self._ds_selected.sel(x=x, y=y, time=t, method='nearest')
        # only create plot if valid
        if np.all(np.isnan(self._data)):
            return
        # if only returning data
        if ax is None:
            return self
        # drop unpassable keyword arguments
        kwargs.pop('cmap') if ('cmap' in kwargs.keys()) else None
        # create legend with geometry name or geolocation
        if ('legend' in kwargs.keys()):
            add_legend = True
            kwargs.pop('legend')
        else:
            add_legend = False
        # create time series plot
        self._line, = ax.plot(self._time, self._data, **kwargs)
        # set labels and title
        ax.set_xlabel('{0} [{1}]'.format('time', 'years'))
        ax.set_ylabel('{0} [{1}]'.format(self._longname, self._units))
        ax.set_title(self._variable)
        # add legend
        if add_legend:
            label = u'{0:8.4f}\u00B0N, {1:8.4f}\u00B0E'.format(lat, lon)
            self._line.set_label(self.properties.get('name') or label)
            linewidth = 6 if (ax.get_legend() is not None) else 0
            lgd = ax.legend(loc=0, frameon=False)
            for line in lgd.get_lines():
                line.set_linewidth(linewidth)
        # set axis ticks to not use constant offset
        ax.xaxis.get_major_formatter().set_useOffset(False)
        return self

    def transect(self, ax, **kwargs):
        """Extracts and plots a time series for a transect

        Parameters
        ----------
        ax : obj or NoneType
            Figure axis on which to plot

            Will only extract time series if ``None``
        cmap : str or NoneType, default None
            matplotlib colormap
        legend : bool, default False
            Add legend with time values
        """
        # convert linestring to dataset coordinate reference system
        lon, lat = np.transpose(self.geometry['coordinates'])
        x, y = rasterio.warp.transform(self.crs, self._ds.rio.crs, lon, lat)
        # get coordinates of each grid cell
        gridx, gridy = np.meshgrid(self._ds.x, self._ds.y)
        # clip ice area to geometry
        if ('cell_area' in self._ds):
            ice_area = self._ds['cell_area'].rio.clip([self.geometry], self.crs, drop=False)
        elif ('ice_area' in self._ds):
            ice_area = self._ds['ice_area'].rio.clip([self.geometry], self.crs, drop=False)
        else:
            raise NameError('No ice area variable in dataset')
        # create valid mask from ice area
        if (ice_area.ndim == 3) and ('band' in ice_area.dims):
            mask = np.isfinite(ice_area.sel(band=1))
        elif (ice_area.ndim == 3) and ('time' in ice_area.dims):
            mask = np.isfinite(ice_area).any(dim='time')
        elif (ice_area.ndim == 2):
            mask = np.isfinite(ice_area)
        # only create plot if valid
        if np.all(np.logical_not(mask)):
            return
        # valid values in mask
        ii, jj = np.nonzero(mask)
        # calculate distances to first point in geometry
        distance = np.sqrt((gridx[mask] - x[0])**2 + (gridy[mask] - y[0])**2)
        # sort output data by distance
        indices = np.argsort(distance)
        self._dist = distance[indices]
        # output reduced time series for each point
        self._data = np.zeros((np.count_nonzero(mask), len(self._ds.time)))
        labels = [None]*len(self._ds.time)
        # for each step in the time series
        for i, t in enumerate(self._ds.time):
            clipped = self._ds_selected.sel(time=t).where(mask, drop=False)
            reduced = clipped.chunk(dict(y=-1,x=-1)).values[ii, jj]
            # sort data based on distance to first point
            self._data[:, i] = reduced[indices]
            labels[i] = '{0:0.2f}'.format(self._time[i].data)
        # only create plot if valid
        if np.all(np.isnan(self._data)):
            return
        # if only returning data
        if ax is None:
            return self
        # get colormap for each time point
        if ('cmap' in kwargs.keys()):
            cmap = copy.copy(plt.cm.get_cmap(kwargs['cmap']))
            # create iterable plot colors for color map
            plot_colors = iter(cmap(np.linspace(0, 1, len(self._ds.time))))
            kwargs.pop('cmap')
        else:
            plot_colors = None
        # create legend for time values
        if ('legend' in kwargs.keys()):
            add_legend = True
            kwargs.pop('legend')
        else:
            add_legend = False
        # output time series plot
        self._line = [None]*len(self._ds.time)
        # for each step in the time series
        for i, t in enumerate(self._ds.time):
            # select color
            if (plot_colors is not None):
                kwargs['color'] = next(plot_colors)
            # create transect plot
            self._line[i], = ax.plot(self._dist, self._data[:,i],
                label=labels[i], **kwargs)
        # set labels and title
        ax.set_xlabel('{0} [{1}]'.format('Distance', 'meters'))
        ax.set_ylabel('{0} [{1}]'.format(self._longname, self._units))
        ax.set_title(self._variable)
        # create legend
        if add_legend:
            lgd = ax.legend(loc=2, frameon=False,
                bbox_to_anchor=(1.025, 1),
                borderaxespad=0.0)
            for line in lgd.get_lines():
                line.set_linewidth(6)
        # set axis ticks to not use constant offset
        ax.xaxis.get_major_formatter().set_useOffset(False)
        return self

    def average(self, ax, **kwargs):
        """Extracts and plots a time series for a regional average

        Parameters
        ----------
        ax : obj or NoneType
            Figure axis on which to plot

            Will only extract time series if ``None``
        legend : bool, default False
            Add legend
        """
        # clip ice area to geometry
        if ('cell_area' in self._ds):
            ice_area = self._ds['cell_area'].rio.clip([self.geometry], self.crs, drop=False)
        elif ('ice_area' in self._ds):
            ice_area = self._ds['ice_area'].rio.clip([self.geometry], self.crs, drop=False)
        else:
            raise NameError('No ice area variable in dataset')
        # create valid mask from ice area
        if (ice_area.ndim == 3) and ('band' in ice_area.dims):
            mask = np.isfinite(ice_area.sel(band=1))
        elif (ice_area.ndim == 3) and ('time' in ice_area.dims):
            mask = np.isfinite(ice_area).any(dim='time')
        elif (ice_area.ndim == 2):
            mask = np.isfinite(ice_area)
        # only create plot if valid
        if np.all(np.logical_not(mask)):
            return
        # list of optional error variables
        error_variables = ('delta_h_sigma',
            'misfit_rms',
            'misfit_rms_scaled',
            'dhdt_sigma'
        )
        # output average time series
        self._data = np.zeros_like(self._ds.time)
        self._area = np.zeros_like(self._ds.time)
        # reduce dataset to geometry
        for i, t in enumerate(self._ds.time):
            # reduce data to time and clip to geometry
            clipped = self._ds_selected.sel(time=t).where(mask, drop=False)
            # reduce cell area to time (for Release-02 and above)
            if (ice_area.ndim == 3) and ('time' in ice_area.dims):
                area = ice_area.sel(time=t)
            else:
                area = ice_area.copy()
            # calculate regional average
            if self._variable in error_variables:
                self._data[i] = np.sqrt(np.sum(area*clipped**2)/np.sum(area))
            else:
                self._data[i] = np.sum(area*clipped)/np.sum(area)
            # calculate total area for region
            self._area[i] = np.sum(area)
        # only create plot if valid
        if np.all(np.isnan(self._data)):
            return
        # if only returning data
        if ax is None:
            return self
        # drop unpassable keyword arguments
        kwargs.pop('cmap') if ('cmap' in kwargs.keys()) else None
        # create legend with geometry name
        if ('legend' in kwargs.keys()) and self.properties.get('name'):
            add_legend = True
        else:
            add_legend = False
        kwargs.pop('legend') if ('legend' in kwargs.keys()) else None
        # create average time series plot
        self._line, = ax.plot(self._time, self._data, **kwargs)
        # set labels and title
        ax.set_xlabel('{0} [{1}]'.format('time', 'years'))
        ax.set_ylabel('{0} [{1}]'.format(self._longname, self._units))
        ax.set_title(self._variable)
        # add legend
        if add_legend:
            self._line.set_label(self.properties.get('name'))
            linewidth = 6 if (ax.get_legend() is not None) else 0
            lgd = ax.legend(loc=0, frameon=False)
            for line in lgd.get_lines():
                line.set_linewidth(linewidth)
        # set axis ticks to not use constant offset
        ax.xaxis.get_major_formatter().set_useOffset(False)
        return self

@xr.register_dataset_accessor('transect')
class Transect(HasTraits):
    """A xarray.DataArray extension for extracting a transect

    Parameters
    ----------
    ds : obj
        ``xarray.Dataset``

    Attributes
    ----------
    _ds : obj
        ``xarray.Dataset``
    _ds_selected : obj
        ``xarray.Dataset`` for selected variable
    _variable : str
        Selected variable
    geometry : dict
        GeoJSON geometry of feature
    properties : dict
        GeoJSON properties of feature
    crs : str
        Coordinate Reference System of feature
    _data : float
        Variable value at geometry
    _dist : str
        Eulerian distance from first point (``LineString``)
    _units : str
        Units of selected variable
    _longname : str
        Unit longname of selected variable
    _line : str
        Matplotlib line object from plot
    """

    def __init__(self, ds):
        # initialize feature
        self.geometry = {}
        self.properties = {}
        self.crs = None
        # initialize dataset
        self._ds = ds
        self._ds_selected = None
        self._variable = None
        # initialize data for time series plot
        self._data = None
        self._dist = None
        self._units = None
        self._longname = None
        self._line = None

    # create plot for a transect
    def plot(self, feature,
        variable='h',
        lag=0,
        crs='epsg:4326',
        ax=None,
        figsize=(6, 4),
        **kwargs
        ):
        """Creates a plot for a transect

        Parameters
        ----------
        feature : obj
            GeoJSON feature to extract
        variable : str, default 'h'
            xarray variable to plot
        lag : int, default 0
            Time lag to plot if 3-dimensional
        crs : str, default 'epsg:4326'
            coordinate reference system of geometry
        ax : obj or NoneType, default None
            Figure axis on which to plot

            Mutually exclusive with ``figsize``
        figsize : tuple, default (6,4)
            Dimensions of figure to create
        kwargs : dict, default {}
            Keyword arguments for transect plot
        """
        # set geometry
        self.geometry = feature.get('geometry') or {}
        # set properties with all keys lowercase
        properties = feature.get('properties') or {}
        self.properties = {k.lower(): v for k, v in properties.items()}
        # get coordinate reference system of geometry
        self.crs = crs
        # attempt to get the coordinate reference system of the dataset
        self.get_crs()
        # set figure axis
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
            fig.patch.set_facecolor('white')
        # reduce to variable
        self._variable = copy.copy(variable)
        if (self._ds[self._variable].ndim == 3) and ('time' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable].sel(time=self._ds.time[lag])
        elif (self._ds[self._variable].ndim == 3) and ('band' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable].sel(band=1)
        else:
            self._ds_selected = self._ds[self._variable]
        # extract units
        self._longname = self._ds[self._variable].attrs['long_name'].replace('  ', ' ')
        self._units = self._ds[self._variable].attrs['units'][0]
        # create plot for a given geometry type
        geometry_type = self.geometry.get('type')
        if (geometry_type.lower() == 'linestring'):
            self.transect(ax, **kwargs)
        else:
            raise ValueError(f'Invalid geometry type {geometry_type}')
        # return the class object
        return self

    # extract a time series for a region
    def extract(self, feature,
        variable='h',
        lag=0,
        crs='epsg:4326',
        ):
        """Extract a transect for a geometry

        Parameters
        ----------
        feature : obj
            GeoJSON feature to extract
        variable : str, default 'h'
            xarray variable to extract
        lag : int, default 0
            Time lag to extract if 3-dimensional
        crs : str, default 'epsg:4326'
            coordinate reference system of geometry
        epoch : float, default 2018.0
            Reference epoch for delta times
        """
        # set geometry
        self.geometry = feature.get('geometry') or {}
        # set properties with all keys lowercase
        properties = feature.get('properties') or {}
        self.properties = {k.lower(): v for k, v in properties.items()}
        # get coordinate reference system of geometry
        self.crs = crs
        # attempt to get the coordinate reference system of the dataset
        self.get_crs()
        # reduce to variable
        self._variable = copy.copy(variable)
        if (self._ds[self._variable].ndim == 3) and ('time' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable].sel(time=self._ds.time[lag])
        elif (self._ds[self._variable].ndim == 3) and ('band' in self._ds[self._variable].dims):
            self._ds_selected = self._ds[self._variable].sel(band=1)
        else:
            self._ds_selected = self._ds[self._variable]
        # extract units
        self._longname = self._ds[self._variable].attrs['long_name'].replace('  ', ' ')
        self._units = self._ds[self._variable].attrs['units'][0]
        # create time series for a given geometry type
        geometry_type = self.geometry.get('type')
        if (geometry_type.lower() == 'linestring'):
            self.transect(None)
        else:
            raise ValueError(f'Invalid geometry type {geometry_type}')
        # return the class object
        return self

    def get_crs(self):
        """Attempt to get the coordinate reference system of the dataset
        """
        # get coordinate reference system from grid mapping
        try:
            grid_mapping = self._ds[self._variable].attrs['grid_mapping']
            ds_crs = self._ds[grid_mapping].attrs['crs_wkt']
        except Exception as exc:
            pass
        else:
            self._ds.rio.set_crs(ds_crs)
            return
        # get coordinate reference system from crs attribute
        try:
            ds_crs = self._ds.rio.crs.to_wkt()
        except Exception as exc:
            pass
        else:
            self._ds.rio.set_crs(ds_crs)
            return
        # raise exception
        raise Exception('Unknown coordinate reference system')

    def transect(self, ax, **kwargs):
        """Extracts and plots a transect

        Parameters
        ----------
        ax : obj or NoneType
            Figure axis on which to plot

            Will only extract transect if ``None``
        legend : bool, default False
            Add legend
        """
        # convert linestring to dataset coordinate reference system
        lon, lat = np.transpose(self.geometry['coordinates'])
        x, y = rasterio.warp.transform(self.crs, self._ds.rio.crs, lon, lat)
        # get coordinates of each grid cell
        gridx, gridy = np.meshgrid(self._ds.x, self._ds.y)
        # clip variable to geometry and create mask
        clipped = self._ds_selected.rio.clip([self.geometry], self.crs, drop=False)
        mask = np.isfinite(clipped)
        # only create plot if valid
        if np.all(np.logical_not(mask)):
            return
        # valid values in mask
        ii, jj = np.nonzero(mask)
        # calculate distances to first point in geometry
        distance = np.sqrt((gridx[mask] - x[0])**2 + (gridy[mask] - y[0])**2)
        # sort output data by distance
        indices = np.argsort(distance)
        self._dist = distance[indices]
        # sort data based on distance to first point
        reduced = clipped.chunk(dict(y=-1,x=-1)).values[ii, jj]
        self._data = reduced[indices]
        # only create plot if valid
        if np.all(np.isnan(self._data)):
            return
        # if only returning data
        if ax is None:
            return self
        # create legend with geometry name
        if ('legend' in kwargs.keys()) and self.properties.get('name'):
            add_legend = True
        else:
            add_legend = False
        kwargs.pop('legend') if ('legend' in kwargs.keys()) else None
        # create transect plot
        self._line, = ax.plot(self._dist, self._data, **kwargs)
        # set labels and title
        ax.set_xlabel('{0} [{1}]'.format('Distance', 'meters'))
        ax.set_ylabel('{0} [{1}]'.format(self._longname, self._units))
        ax.set_title(self._variable)
        # add legend
        if add_legend:
            self._line.set_label(self.properties.get('name'))
            linewidth = 6 if (ax.get_legend() is not None) else 0
            lgd = ax.legend(loc=0, frameon=False)
            for line in lgd.get_lines():
                line.set_linewidth(linewidth)
        # set axis ticks to not use constant offset
        ax.xaxis.get_major_formatter().set_useOffset(False)
        return self
