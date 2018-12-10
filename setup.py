import re
from setuptools import setup, find_packages

VERSIONFILE = "fast_autocomplete/__init__.py"
with open(VERSIONFILE, "r") as the_file:
    verstrline = the_file.read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


def get_reqs(filename):
    with open(filename, "r") as reqs_file:
        reqs = reqs_file.readlines()
        reqs = list(map(lambda x: x.replace('==', '>='), reqs))
    return reqs


reqs = get_reqs("requirements.txt")

try:
    with open('README.md') as file:
        long_description = file.read()
except Exception:
    long_description = "Autocomplete"

setup(
    name='fast-autocomplete',
    description='Fast Autocomplete using Directed Word Graph',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Sep Dehpour',
    url='https://github.com/wearefair/fast-autocomplete',
    download_url='https://github.com/wearefair/fast-autocomplete/tarball/master',
    author_email='sepd@fair.com',
    version=verstr,
    install_requires=reqs,
    dependency_links=[],
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    scripts=[],
    test_suite="tests",
    tests_require=['mock'],
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 4 - Beta",
    ]
)
