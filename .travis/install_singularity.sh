#!/bin/bash -ex

if [ ! -x $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
    echo "Installing singularity..."
    SOURCE=/tmp/singularity_source
    apt-get update && sudo apt-get install -y python libarchive-dev squashfs-tools dh-autoreconf build-essential
    export CFLAGS="$(pkg-config --cflags libarchive) $(pkg-config --libs-only-L libarchive) $CFLAGS "
    git clone https://github.com/singularityware/singularity.git $SOURCE
    cd $SOURCE
    git checkout tags/$SINGULARITY_VERSION
    ./autogen.sh
    ./configure --prefix=$TRAVIS_SINGULARITY_PATH --sysconfdir=/etc
    make install
    rm -rf $SOURCE
else
    echo "Singularity is already installed."
fi
