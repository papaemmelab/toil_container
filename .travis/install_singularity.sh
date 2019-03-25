#!/bin/bash -ex

if [ ! -x $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
    echo "Installing singularity..."
    SOURCE=/tmp/singularity_source
    apt-get update && apt-get install -y libarchive-devel libarchive-dev squashfs-tools dh-autoreconf build-essential
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
