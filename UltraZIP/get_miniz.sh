#!/bin/sh
set -eu
mkdir -p vendor
if [ ! -f vendor/miniz/miniz.h ]; then
 git clone --depth 1 --branch 3.0.2 https://github.com/richgel999/miniz.git vendor/miniz
fi
