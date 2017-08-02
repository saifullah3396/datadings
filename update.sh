#!/usr/bin/env bash
set -e

rm *.whl
git pull
./dist.sh
pip install --user -U --no-dependencies *.whl
