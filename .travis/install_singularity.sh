#!/bin/bash -ex

if [ ! -x $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
    echo "Installing singularity..."
    SOURCE=/tmp/singularity_source
    CMD="apt-get update && sudo apt-get install -y python libarchive-dev squashfs-tools dh-autoreconf build-essential"
    echo $CMD
    sudo apt-get update && sudo apt-get install -y python libarchive-dev squashfs-tools dh-autoreconf build-essential
    git clone https://github.com/singularityware/singularity.git $SOURCE
    cd $SOURCE
    git checkout tags/$SINGULARITY_VERSION
    sudo ./autogen.sh
    sudo ./configure --prefix=$TRAVIS_SINGULARITY_PATH --sysconfdir=/etc
    sudo make install
    rm -rf $SOURCE
else
    echo "Singularity is already installed."
fi
