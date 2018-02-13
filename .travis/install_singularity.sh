#!/bin/bash -ex

apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
git clone https://github.com/singularityware/singularity.git
cd singularity
git checkout tags/$SINGULARITY_VERSION
./autogen.sh
./configure --prefix=$TRAVIS_SINGULARITY_PATH
make install
