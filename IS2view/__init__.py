"""
Gridded ICESat-2 Product Viewer for Python
==========================================

IS2view contains a viewer for ICESat-2 ATL14/15 Gridded
Land Ice Height Products

Documentation is available at https://is2view.readthedocs.io
"""
from IS2view.IS2view import widgets, leaflet
from IS2view.convert import convert
import IS2view.utilities
import IS2view.version
# get version
__version__ = IS2view.version.version
