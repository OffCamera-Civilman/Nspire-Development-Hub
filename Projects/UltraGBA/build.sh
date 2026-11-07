#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "$0")" && pwd)
output_dir=$(realpath -m "${1:?Pass an output directory}")
upstream=https://github.com/andymcca/lr-gpsp-nspire.git
revision=2ddeb23b565cab84e20278bb73ed76f3d91b25f5
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
export PATH="$(nspire-tools _toolchainpath):$PATH"

git -C "$work_dir" init -q
git -C "$work_dir" fetch -q --depth=1 "$upstream" "$revision"
git -C "$work_dir" checkout -q --detach FETCH_HEAD
cd "$work_dir"
test "$(git rev-parse HEAD)" = "$revision"
git apply --index --whitespace=nowarn "$project_dir/run001.patch"

make -j2 GENZ='genzehn --name "UltraGBA Run001"'
genzehn --info --input gpsp_libretro.tns
python3 tests/calc_checks.py gpsp_libretro.elf
mkdir -p dist
make-prg gpsp_libretro.tns dist/UltraGBA_Run001.tns
python3 tests/host/rom/make_test_rom.py dist/UltraGBA_Pattern_Run001.gba.tns
make -s -j2 -C tests/host build/gpsp-host
python3 "$project_dir/test_startup.py" tests/host/build/gpsp-host dist/UltraGBA_Pattern_Run001.gba.tns

mkdir -p "$output_dir"
cp dist/UltraGBA_Run001.tns dist/UltraGBA_Pattern_Run001.gba.tns "$output_dir/"
git archive --format=tar.gz --prefix=UltraGBA_Run001/ \
  -o "$output_dir/UltraGBA_Run001-source.tar.gz" "$(git write-tree)"
printf 'Upstream %s\n' "$revision"
arm-none-eabi-gcc -dumpfullversion
sha256sum "$output_dir"/*.tns
