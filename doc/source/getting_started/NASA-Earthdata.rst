==============
NASA Earthdata
==============

NASA Data Distribution Centers
##############################

The NASA Earth Science Data Information Systems Project funds and operates
`12 Distributed Active Archive Centers (DAACs) <https://earthdata.nasa.gov/about/daacs>`_
throughout the United States.
These centers have recently transitioned from ftp to https servers.
The https updates are designed to increase performance and improve security during data retrieval.
NASA Earthdata uses `OAuth2 <https://wiki.earthdata.nasa.gov/pages/viewpage.action?pageId=71700485>`_,
an approach to authentication that protects your personal information.

- https://urs.earthdata.nasa.gov/documentation
- https://wiki.earthdata.nasa.gov/display/EL/Knowledge+Base
- https://nsidc.org/support/how/how-do-i-programmatically-request-data-services
- https://nsidc.org/support/faq/what-options-are-available-bulk-downloading-data-https-earthdata-login-enabled

NSIDC
#####

The `National Snow and Ice Data Center (NSIDC) <https://nsidc.org/daac/>`_ DAAC
provides data and information for snow and ice processes, particularly interactions among snow,
ice, atmosphere, and ocean, in support of research in global change detection and model validation.
NSIDC is migrating its data archive to the Earthdata Cloud, which is hosted in Amazon Web Services (AWS).
If any problems contact NSIDC support at `nsidc@nsidc.org <mailto:nsidc@nsidc.org>`_ or
the NASA EOSDIS support team `support@earthdata.nasa.gov <mailto:support@earthdata.nasa.gov>`_.

Data Access Steps for NSIDC
###########################

1. `Register with NASA Earthdata Login system <https://urs.earthdata.nasa.gov/users/new>`_
2. `After registering, login to the system <https://urs.earthdata.nasa.gov/home>`_
3. Add ``NSIDC_DATAPOOL_OPS`` and ``nsidc-daacdata`` `applications to Earthdata <https://wiki.earthdata.nasa.gov/display/EL/How+To+Pre-authorize+an+application>`_
4. Copy your NASA Earthdata credentials or `create a .netrc file <https://nsidc.org/support/how/v0-programmatic-data-access-guide>`_ to store your credentials permanently

.. code-block:: bash

    echo "machine urs.earthdata.nasa.gov login <uid> password <password>" >> ~/.netrc
    chmod 0600 ~/.netrc

NASA Common Metadata Repository
###############################

The NASA Common Metadata Repository (CMR) is a catalog of all data
and service metadata records contained as part of NASA's Earth
Observing System Data and Information System (EOSDIS).
Querying the CMR system is a way of quickly performing a search
through the NASA Earthdata archive.
Basic queries for the granule names and NSIDC URLs of NASA ICESat-2
data are available through the ``cmr`` routine in the ``utilities`` module.
For AWS instances in ``us-west-2``, CMR queries can access urls for S3 endpoints.

.. code-block:: python

    ids,urls = IS2view.utilities.cmr(product='ATL15', release='001',
        regions='AA', resolutions='01km', verbose=False)

Other Data Access Examples
##########################

- `Curl and Wget <https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+cURL+And+Wget>`_
- `Python <https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python>`_
- `Jupyter <https://github.com/nsidc/NSIDC-Data-Access-Notebook>`_
- `icepyx <https://github.com/icesat2py/icepyx>`_
