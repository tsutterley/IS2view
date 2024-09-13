======================
Setup and Installation
======================

``IS2view`` is available for download from the `GitHub repository <https://github.com/tsutterley/IS2view>`_,
the `Python Package Index (pypi) <https://pypi.org/project/IS2view/>`_,
and from `conda-forge <https://anaconda.org/conda-forge/is2view>`_.

The simplest installation for most users will likely be using ``conda``:

.. code-block:: bash

    conda install -c conda-forge is2view

``conda`` installed versions of ``IS2view`` can be upgraded to the latest stable release:

.. code-block:: bash

    conda update is2view

To use the development repository, please fork ``IS2view`` into your own account and then clone onto your system:

.. code-block:: bash

    git clone https://github.com/tsutterley/IS2view.git

``IS2view`` can then be installed within the package directory using ``pip``:

.. code-block:: bash

    python3 -m pip install --user .

To include all optional dependencies:

.. code-block:: bash

   python3 -m pip install --user .[all]

The development version of ``IS2view`` can also be installed directly from GitHub using ``pip``:

.. code-block:: bash

    python3 -m pip install --user git+https://github.com/tsutterley/IS2view.git
