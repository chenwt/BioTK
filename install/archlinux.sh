#!/usr/bin/env bash

pkgs=(base base-devel parallel lz4 pigz cython)
aur_pkgs=(pixz datamash tokyocabinet)

# Python packages
for pkg in $(cat $(realpath $(dirname $0))/../requirements.txt | grep -v '#'); do
    pacman -Ss "^python-$pkg$" > /dev/null && pkgs+=(python-$pkg)
done

install_packer() {
    tmp=$(mktemp -d)
    trap 'rm -rf $tmp'
    cd $tmp
    bash <(curl aur.sh) -S packer
    cd packer
    sudo pacman -U *.pkg.*
}

which packer 2> /dev/null || install_packer

yes '' | sudo pacman -S --needed ${pkgs[@]}

for pkg in ${aur_pkgs[@]}; do
    pacman -Qi $pkg 1> /dev/null 2> /dev/null \
        || packer -S --noconfirm --noedit $pkg
done
