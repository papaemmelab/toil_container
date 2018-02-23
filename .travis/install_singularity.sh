#!/bin/bash -ex

if [ ! -x $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
    echo "Installing singularity..."
    sudo apt-get update
    sudo apt-get install squashfs-tools dh-autoreconf build-essential
    SOURCE=/tmp/singularity_source
    git clone https://github.com/singularityware/singularity.git $SOURCE
    cd $SOURCE
    git checkout tags/$SINGULARITY_VERSION
    ./autogen.sh
    ./configure --prefix=$TRAVIS_SINGULARITY_PATH
    make install
    rm -rf $SOURCE
else
    echo "Singularity is already installed."
fi

if [ ! -f $CACHED_SINGULARITY_IMAGE ]; then
    sudo apt-get update
    sudo apt-get install squashfs-tools dh-autoreconf build-essential
    sudo $TRAVIS_SINGULARITY_PATH/bin/singularity build $CACHED_SINGULARITY_IMAGE docker://ubuntu:latest
fi
