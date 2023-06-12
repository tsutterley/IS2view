#!/usr/bin/env python
u"""
version.py (04/2021)
Gets semantic version number and commit hash from setuptools-scm
"""
from pkg_resources import get_distribution

# get semantic version from setuptools-scm
version = get_distribution("IS2view").version
# append "v" before the version
full_version = f"v{version}"
# get project name
project_name = get_distribution("IS2view").project_name
