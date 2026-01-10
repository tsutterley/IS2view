=======
Testing
=======

``IS2view`` uses the ``pytest`` framework to run tests and verify outputs.
Running the test suite requires a `dev installation <../getting_started/Install.html>`_ of the ``IS2view`` package to include all of the optional dependencies.

.. code-block:: bash

    python -m pip install --editable '.[dev]'

Continuous Integration
^^^^^^^^^^^^^^^^^^^^^^
We use `GitHub Actions <https://github.com/tsutterley/IS2view/actions>`_ continuous integration (CI) services to build and test the project on Linux (``ubuntu-latest``), Mac (``macos-latest``), and Windows (``windows-latest``) Operating Systems.
The configuration files for this service are in the `GitHub workflows <https://github.com/tsutterley/IS2view/tree/main/.github/workflows>`_ directory.
Most of the workflows use ``pixi`` to install the required dependencies and build the custom environment.

The GitHub Actions jobs include:

* Verifying that the code meets style guidelines using `ruff <https://docs.astral.sh/ruff/>`_
* Running `flake8 <https://flake8.pycqa.org/en/latest/>`_ to check the code for compilation errors
* Uploading source and wheel distributions to `PyPI <https://pypi.org/project/IS2view/>`_ (on releases)
