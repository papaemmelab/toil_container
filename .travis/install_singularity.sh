#!/bin/bash -ex

if [ ! -x $TRAVIS_SINGULARITY_PATH/singularity/bin/singularity ]; then
    echo "Installing singularity..."
    apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
    git clone https://github.com/singularityware/singularity.git
    cd singularity
    git checkout tags/$SINGULARITY_VERSION
    ./autogen.sh
    ./configure --prefix=$TRAVIS_SINGULARITY_PATH
    make install
else
    echo "Singularity is already installed."
fi
