from setuptools import setup

# get version
with open('version.txt', mode='r', encoding='utf8') as fh:
    fallback_version = fh.read()

# semantic version configuration for setuptools-scm
setup_requires = ["setuptools_scm"]
use_scm_version = {
    "relative_to": __file__,
    "local_scheme": "node-and-date",
    "version_scheme": "python-simplified-semver",
    "fallback_version":fallback_version,
}

setup(
    name='IS2view',
    use_scm_version=use_scm_version
)
