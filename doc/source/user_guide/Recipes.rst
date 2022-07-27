.. _recipes:

=======
Recipes
=======

Add Contextual Layers
#####################

- `ArcticDEM <https://www.pgc.umn.edu/data/arcticdem>`_ (NSIDC Sea Ice Polar Stereographic North, `EPSG:3413 <https://epsg.io/3413>`_)

.. code-block:: python

   m.add(IS2view.image_service_layer('ArcticDEM'))

- `Reference Elevation Model of Antarctica <https://www.pgc.umn.edu/data/rema>`_ (Antarctic Polar Stereographic, `EPSG:3031 <https://epsg.io/3031>`_)

.. code-block:: python

   m.add(IS2view.image_service_layer('REMA'))

Plot a Transect
###############

.. code-block:: python

   import geopandas
   # read shapefile of glacial flowlines
   gdf = geopandas.read_file('/vsizip/shapefiles.zip/glacier0001.shp')
   # add geodataframe
   m.add_geodataframe(gdf)
   for feature in m.geometries['features']:
      ds.timeseries.plot(feature, cmap='rainbow', legend=True,
         variable=IS2widgets.variable.value,
      )

.. figure:: ../_assets/transect.png
   :width: 400
   :align: center

   Greenland glacier flowlines from `Felikson et al. (2020) <https://zenodo.org/record/4284759>`_

Plot Multiple Time Series
#########################

.. code-block:: python

   import fiona
   fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
   import geopandas
   import numpy as np
   import matplotlib.pyplot as plt
   # read kml file with subglacial lake outlines
   gdf = geopandas.read_file('lake_outlines.kml')
   # add geodataframe of Whillians ice stream subglacial lakes
   m.add_geodataframe(gdf[gdf['names'].str.startswith('Whillians')])
   # create figure axis
   fig, ax = plt.subplots()
   fig.patch.set_facecolor('white')
   # plot colors for each geometry
   n_features = len(m.geometries['features'])
   plot_colors = iter(plt.cm.rainbow_r(np.linspace(0,1,n_features)))
   for geo in m.geometries['features']:
      color = next(plot_colors)
      ds.timeseries.plot(geo, ax=ax,
         variable=IS2widgets.variable.value,
         color=color
      )
   # show combined plot
   plt.show()

.. figure:: ../_assets/multiple.png
   :width: 400
   :align: center

   Antarctic subglacial lake delineations from `Fricker et al. (2007) <https://doi.org/10.1126/science.1136897>`_

Calculate Area Averages
#######################

.. code-block:: python

   import geopandas
   import numpy as np
   import matplotlib.pyplot as plt
   # read shapefile with drainage outlines
   gdf = geopandas.read_file('IceBoundaries_Antarctica_v02.shp')
   # add geodataframe of drainages of the Amundsen Sea Embayment
   m.add_geodataframe(gdf[(gdf['Subregions'] == 'G-H') & (gdf['TYPE'] == 'GR')])
   # allocate for combined area and volume
   area = np.zeros_like(ds.time, dtype=np.float64)
   volume = np.zeros_like(ds.time, dtype=np.float64)
   for geo in m.geometries['features']:
      ds.timeseries.plot(geo, legend=True,
         variable=IS2widgets.variable.value,
      )
      # add to total area and volume
      area += ds.timeseries._area
      volume += ds.timeseries._area*ds.timeseries._data
   # create output figure
   fig, ax = plt.subplots()
   fig.patch.set_facecolor('white')
   ax.plot(ds.timeseries._time, volume/area)
   ax.set_xlabel('{0} [{1}]'.format('time', 'years'))
   ax.set_ylabel('{0} [{1}]'.format(ds.timeseries._longname, ds.timeseries._units))
   ax.set_title('average {0}'.format(ds.timeseries._variable))
   # show average plot
   plt.show()

.. figure:: ../_assets/average.png
   :width: 400
   :align: center

   MEaSUREs Antarctic Boundaries from `Mouginot et al. (2017) <https://nsidc.org/data/NSIDC-0709/versions/2>`_

