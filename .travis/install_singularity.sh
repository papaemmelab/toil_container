#!/bin/bash -ex

export TRAVIS_SINGULARITY_PATH=/home/travis/build/leukgen/toil_container/singularity
export PATH=$PATH:$TRAVIS_SINGULARITY_PATH/bin

if [ ! -x $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
    apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
    git clone https://github.com/singularityware/singularity.git
    cd singularity
    ./autogen.sh
    ./configure --prefix=$TRAVIS_SINGULARITY_PATH
    make install
else
    echo exists
fi
