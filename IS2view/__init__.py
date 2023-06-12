"""
Gridded ICESat-2 Product Viewer for Python
==========================================

Interactive visualization and data extraction tool for the
ICESat-2 ATL14/15 Gridded Land Ice Height Products

Documentation is available at https://is2view.readthedocs.io
"""
import IS2view.utilities
import IS2view.version
from IS2view.convert import convert
from IS2view.io import from_file, from_rasterio, from_xarray
from IS2view.tools import widgets
from IS2view.visualization import leaflet, layers, image_service_layer
# get semantic version from setuptools-scm
__version__ = IS2view.version.version
