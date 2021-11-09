#!/usr/bin/env python3
from setuptools import setup, find_packages
import subprocess

# Use tag as version, *if* it is a tagged commit...
r = subprocess.run(['git', 'tag', '--points-at=HEAD'], stdout=subprocess.PIPE)
version = r.stdout.rstrip().decode('UTF-8')

# ...otherwise, use abbreviated git commit hash
if version == '':
    r = subprocess.run(['git', 'rev-parse', '--short=8', 'HEAD'], stdout=subprocess.PIPE)
    version = r.stdout.rstrip().decode('UTF-8')

setup(
    name='vss-tools',
    version=version,
    description='COVESA Vehicle Signal Specification tooling.',
    url='https://github.com/COVESA/vss-tools',
    license='Mozilla Public License v2',
    packages=find_packages(exclude=('tests', 'contrib')),
    scripts=['vspec2csv.py', 'vspec2franca.py', 'vspec2binary.py', 'vspec2json.py', 'vspec2yaml.py', 'contrib/vspec2c.py', 'contrib/vspec2protobuf.py', 'contrib/ocf/vspec2ocf.py'],
    python_requires='>=3.7',
    install_requires=['pyyaml>=5.1', 'anytree>=2.8.0', 'stringcase>=1.2.0', 'deprecation>=2.1.0'],
    tests_require=['pytest>=2.7.2'],
)
