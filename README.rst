=======
IS2view
=======

|Language|
|License|
|Documentation Status|
|Binder|
|Pangeo|

.. |Language| image:: https://img.shields.io/badge/python-v3.8-green.svg
   :target: https://www.python.org/

.. |License| image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://github.com/tsutterley/IS2view/blob/main/LICENSE

.. |Documentation Status| image:: https://readthedocs.org/projects/is2view/badge/?version=latest
   :target: https://is2view.readthedocs.io/en/latest/?badge=latest

.. |Binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/tsutterley/IS2view/main

.. |Pangeo| image:: https://img.shields.io/static/v1.svg?logo=Jupyter&label=PangeoBinderAWS&message=us-west-2&color=orange
   :target: https://aws-uswest2-binder.pangeo.io/v2/gh/tsutterley/IS2view/main?urlpath=lab

Interactive visualization and data extraction tool for ICESat-2 ATL14/15 Gridded Land Ice Height Products

- https://icesat-2.gsfc.nasa.gov
- https://icesat-2-scf.gsfc.nasa.gov
- https://nsidc.org/data/icesat-2/

Dependencies
############

- `boto3: Amazon Web Services (AWS) SDK for Python <https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`_
- `bottleneck: Fast NumPy array functions written in C <https://github.com/pydata/bottleneck>`_
- `dask: Parallel computing with task scheduling <https://www.dask.org/>`_
- `ipyleaflet: Interactive maps in the Jupyter notebook <https://ipyleaflet.readthedocs.io/en/latest/>`_
- `matplotlib: Python 2D plotting library <https://matplotlib.org/>`_
- `netCDF4: Python interface to the netCDF C library <https://unidata.github.io/netcdf4-python/>`_
- `numpy: Scientific Computing Tools For Python <https://numpy.org>`_
- `rioxarray: geospatial xarray extension powered by rasterio <https://github.com/corteva/rioxarray>`_
- `s3fs: Pythonic file interface to S3 built on top of botocore <https://s3fs.readthedocs.io/en/latest/>`_
- `xarray: N-D labeled arrays and datasets in Python <https://docs.xarray.dev/en/stable/>`_

Download
########

| The program homepage is:
| https://github.com/tsutterley/IS2view
| A zip archive of the latest version is available directly at:
| https://github.com/tsutterley/IS2view/archive/main.zip

Disclaimer
##########

This project contains work and contributions from the `scientific community <./CONTRIBUTORS.rst>`_.
This program is not sponsored or maintained by the Universities Space Research Association (USRA) or NASA.
It is provided here for your convenience but *with no guarantees whatsoever*.

License
#######

The content of this project is licensed under the
`Creative Commons Attribution 4.0 Attribution license <https://creativecommons.org/licenses/by/4.0/>`_
and the source code is licensed under the `MIT license <LICENSE>`_.
