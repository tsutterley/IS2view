======================
Setup and Installation
======================

Currently, ``IS2view`` is only available for download from the `GitHub repository <https://github.com/tsutterley/IS2view>`_.
The contents of the repository can be download as a
`zipped file <https://github.com/tsutterley/IS2view/archive/main.zip>`_  or cloned.
To use this repository, please fork into your own account and then clone onto your system.

.. code-block:: bash

    git clone https://github.com/tsutterley/IS2view.git

Can then install using ``setuptools``

.. code-block:: bash

    python setup.py install

or ``pip``

.. code-block:: bash

    python3 -m pip install --user .

Alternatively can install the utilities directly from GitHub with ``pip``:

.. code-block:: bash

    python3 -m pip install --user git+https://github.com/tsutterley/IS2view.git

| This repository can be also tested using `BinderHub <https://github.com/jupyterhub/binderhub>`_ platforms:
| |Binder| |Pangeo|

.. |Binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/tsutterley/IS2view/main

.. |Pangeo| image:: https://img.shields.io/static/v1.svg?logo=Jupyter&label=PangeoBinderAWS&message=us-west-2&color=orange
   :target: https://aws-uswest2-binder.pangeo.io/v2/gh/tsutterley/IS2view/main?urlpath=lab
