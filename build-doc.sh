#!/bin/bash
set -e -x

cd doc
rm -rf out source/generated
python3.6 -m sphinx -b html source out
rm -rf out/.doctrees
cd ..
