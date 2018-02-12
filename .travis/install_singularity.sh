#!/bin/bash -ex

sudo apt-get update && sudo apt-get install squashfs-tools dh-autoreconf build-essential
git clone https://github.com/singularityware/singularity.git
cd singularity
./autogen.sh
./configure --prefix=/usr/local
sudo make install
make test
sudo chmod g+x /usr/local/bin/singularity
