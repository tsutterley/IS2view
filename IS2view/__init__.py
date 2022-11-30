"""
Gridded ICESat-2 Product Viewer for Python
==========================================

Interactive visualization and data extraction tool for the
ICESat-2 ATL14/15 Gridded Land Ice Height Products

Documentation is available at https://is2view.readthedocs.io
"""
from IS2view.IS2view import widgets, leaflet, layers, image_service_layer
from IS2view.convert import convert
from IS2view.io import from_file, from_rasterio, from_xarray
import IS2view.utilities
import IS2view.version
# get version
__version__ = IS2view.version.version
