#!/usr/bin/env python3
from distutils.core import setup
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
    description='GENIVI Vehicle Signal Specification tooling.',
    url='https://github.com/GENIVI/vss-tools',
    license='Mozilla Public License v2',
    py_modules=['vspec'],
    scripts=['vspec2csv.py', 'vspec2franca.py', 'vspec2binary.py', 'vspec2json.py', 'contrib/vspec2c.py', 'contrib/vspec2protobuf.py', 'contrib/ocf/vspec2ocf.py'],
    python_requires='>=3.4'
)
