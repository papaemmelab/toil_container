#!/bin/bash -ex

if [ ! -f $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
    apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
    git clone https://github.com/singularityware/singularity.git
    cd singularity
    ./autogen.sh
    ./configure --prefix=$TRAVIS_SINGULARITY_PATH
    make install
else
    echo exists
fi
