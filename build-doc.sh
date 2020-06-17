#!/bin/bash
set -e -x

cd doc
rm -rf out source/generated
SPHINX_APIDOC_OPTIONS=members,show-inheritance sphinx-apidoc \
  --module-first \
  --separate \
  --maxdepth 6 \
  --no-toc \
  --output-dir source/generated \
  ../datadings
python3.6 -m sphinx -b html source out
rm -rf out/.doctrees
cd ..
