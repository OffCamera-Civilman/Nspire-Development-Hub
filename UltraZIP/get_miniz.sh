#!/bin/sh
set -eu
mkdir -p vendor
if [ ! -f vendor/miniz/miniz.h ]; then
  git clone --depth 1 --branch 3.0.2 https://github.com/richgel999/miniz.git vendor/miniz
fi
# miniz 3.x expects this CMake-generated export header, which is absent in the source checkout.
cat > vendor/miniz/miniz_export.h <<'EOF'
#ifndef MINIZ_EXPORT_H
#define MINIZ_EXPORT_H
#define MINIZ_EXPORT
#endif
EOF
test -s vendor/miniz/miniz_export.h
printf 'miniz ready: vendor/miniz\n'
