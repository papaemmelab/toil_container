#!/bin/bash -ex

export PATH=$HOME/singularity/bin:$PATH

if which singularity > /dev/null; then
    echo exists
else
    sudo apt-get update && sudo apt-get install squashfs-tools dh-autoreconf build-essential
    git clone https://github.com/singularityware/singularity.git
    cd singularity
    ./autogen.sh
    ./configure --prefix=$HOME/singularity
    sudo make install
fi
