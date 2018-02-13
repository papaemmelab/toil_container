#!/bin/bash -ex

<<<<<<< HEAD
if [ ! -x $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
    echo "Installing singularity..."
    SOURCE=/tmp/singularity_source
=======
if [ ! -f $TRAVIS_SINGULARITY_PATH/bin/singularity ]; then
>>>>>>> :wrench: fix condition
    apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
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
