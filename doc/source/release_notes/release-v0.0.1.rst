##################
`Release v0.0.1`__
##################

* ``fix``: pin ``s3fs`` to prevent ``boto3`` incompatibility issue
* ``refactor``: using ``pathlib`` to define and expand paths (`#23 <https://github.com/tsutterley/IS2view/pull/23>`_)
* ``feat``: add functions to retrieve and revoke NASA Earthdata User tokens (`#23 <https://github.com/tsutterley/IS2view/pull/23>`_)
* ``fix``: add from future annotations to ``utilities`` (`#23 <https://github.com/tsutterley/IS2view/pull/23>`_)
* ``refactor``: update ``postBuild`` with release of ``ipyleatlas-s3aflet`` (`#23 <https://github.com/tsutterley/IS2view/pull/23>`_)
* ``fix``: update ``postBuild`` for ``yarn`` error `yarnpkg/berry#4570 <https://github.com/yarnpkg/berry/issues/4570>`_ (`#22 <https://github.com/tsutterley/IS2view/pull/22>`_)
* ``fix``: set import ``warnings`` to ``"module"`` (`#21 <https://github.com/tsutterley/IS2view/pull/21>`_)
* ``feat``: add functions for managing and maintaining ``git`` repositories (`#20 <https://github.com/tsutterley/IS2view/pull/20>`_)
* ``feat``: added case for warping input image (`#19 <https://github.com/tsutterley/IS2view/pull/19>`_)
* ``fix``: add ``zarr`` to dependencies
* ``docs``: add recipe for setting AWS credentials
* ``docs``: slimmer build to prevent overutilization (`#18 <https://github.com/tsutterley/IS2view/pull/18>`_)
* ``docs``: add data citations (`#18 <https://github.com/tsutterley/IS2view/pull/18>`_)
* ``refactor``: new s3 path for ``atlas-s3`` asset (`#18 <https://github.com/tsutterley/IS2view/pull/18>`_)
* ``feat``: add ``io`` module for reading from ``zarr`` files (`#17 <https://github.com/tsutterley/IS2view/pull/17>`_)
* ``docs``: update Getting Started with R002 links
* ``docs``: update Resources with R002 links
* ``docs``: add data product tables
* ``docs``: slimmer builds to prevent RTD overutilization
* ``refactor``: update ``postBuild`` for ``ipyleaflet`` clone
* ``fix``: ``postBuild`` to add ``webpack yarn install`` (`#16 <https://github.com/tsutterley/IS2view/pull/16>`_)
* ``feat``: public release of NSIDC s3 access (`#16 <https://github.com/tsutterley/IS2view/pull/16>`_)
* ``docs``: add getting started guide (`#15 <https://github.com/tsutterley/IS2view/pull/15>`_)
* ``fix``: add get ``crs`` function to ``leaflet``
* ``feat``: add query granules for local and s3 (`#14 <https://github.com/tsutterley/IS2view/pull/14>`_)
* ``docs``: update average plot recipe for all regions (`#13 <https://github.com/tsutterley/IS2view/pull/13>`_)
* ``docs``: add attributes and parameters for classes (`#12 <https://github.com/tsutterley/IS2view/pull/12>`_)
* ``feat``: add function for DEM image service layers (`#11 <https://github.com/tsutterley/IS2view/pull/11>`_)
* ``refactor``: ice_area for R002 (`#2 <https://github.com/tsutterley/IS2view/pull/2>`_)
* ``docs``: add some documented recipes (`#10 <https://github.com/tsutterley/IS2view/pull/10>`_)
* ``refactor``: save entire geojson feature in drawn geometries (`#9 <https://github.com/tsutterley/IS2view/pull/9>`_)
* ``feat``: can save geometry features to file (`#9 <https://github.com/tsutterley/IS2view/pull/9>`_)
* ``feat``: add transect class for ATL14 data extraction (`#9 <https://github.com/tsutterley/IS2view/pull/9>`_)
* ``fix``: increase ``numpy`` version for compatibility with ``xarray`` 2022.06.0 (`#9 <https://github.com/tsutterley/IS2view/pull/9>`_)
* ``feat``: add widgets for ATL14/15 release and ATL15 resolution (`#8 <https://github.com/tsutterley/IS2view/pull/8>`_)
* ``feat``: can use variable ``cell_areas`` (for ATL15 Release-02) (`#8 <https://github.com/tsutterley/IS2view/pull/8>`_)
* ``feat``: can add ``geopandas`` ``GeoDataFrames`` to maps to calculate regional time series (`#8 <https://github.com/tsutterley/IS2view/pull/8>`_)
* ``refactor``: only add textual popups for the added layer (`#8 <https://github.com/tsutterley/IS2view/pull/8>`_)
* ``feat``: add transect plot (`#7 <https://github.com/tsutterley/IS2view/pull/7>`_)
* ``feat``: add optional background layers (`#7 <https://github.com/tsutterley/IS2view/pull/7>`_)
* ``feat``: add ``postBuild`` with ``imageservice`` (`#6 <https://github.com/tsutterley/IS2view/pull/6>`_)
* ``feat``: observe changes in ATL15 time lag (`#5 <https://github.com/tsutterley/IS2view/pull/5>`_)
* ``feat``: add draw control for extracting geometries (`#5 <https://github.com/tsutterley/IS2view/pull/5>`_)
* ``docs``: add initial user documentation (`#4 <https://github.com/tsutterley/IS2view/pull/4>`_)
* ``feat``: add conversion module to convert to ``zarr`` (`#4 <https://github.com/tsutterley/IS2view/pull/4>`_)
* ``docs``: minimize build to prevent overutilization (`#4 <https://github.com/tsutterley/IS2view/pull/4>`_)
* ``refactor``: use ``imshow`` from ``xarray`` (`#3 <https://github.com/tsutterley/IS2view/pull/3>`_)
* ``feat``: enable contextual popups (`#2 <https://github.com/tsutterley/IS2view/pull/2>`_)
* ``feat``: add initial github actions workflow (`#1 <https://github.com/tsutterley/IS2view/pull/1>`_)
* ``feat``: initial commit |tada|

.. __: https://github.com/tsutterley/IS2view/releases/tag/0.0.1

.. |tada|    unicode:: U+1F389 .. 	PARTY POPPER
