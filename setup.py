#!/usr/bin/env python3
from setuptools import setup, find_packages

# Proposed versioning mechanism
#
# General: - Use 3 numbers only if needed, i.e. do not use X.Y.0
#          - Master branch should by default always have a dev-version, except for released commits
#
# * During development (in master), use X.Y.devN, use N==0 as starting point, only increase N if needed for pypi
#   reasons, like if a maintainer has pushed 4.0.dev0 to pypi, then update to 4.0.dev1
# * For release candidates use X.YrcN, use N==0 as starting point
# * If needed (for bigger functionality, dependencies, .., create pre-releases like 0.4a0
# * When working on patches just add a third number, like 0.4.1.dev0, 0.4.1rc0 (if needed at all)
#
#

setup(
    name='vss-tools',
    description='COVESA Vehicle Signal Specification tooling.',
    version='4.1.dev5',
    url='https://github.com/COVESA/vss-tools',
    license='Mozilla Public License 2.0',
    packages=find_packages(exclude=('tests', 'contrib')),
    scripts=['vspec2csv.py', 'vspec2x.py', 'vspec2franca.py', 'vspec2json.py', 'vspec2ddsidl.py',
             'vspec2yaml.py', 'vspec2protobuf.py', 'vspec2graphql.py'],
    python_requires='>=3.8',
    install_requires=['pyyaml>=5.1', 'anytree>=2.8.0', 'deprecation>=2.1.0', 'graphql-core'],
    tests_require=['pytest>=2.7.2'],
    package_data={'vspec': [
        'py.typed'
    ]},
)
