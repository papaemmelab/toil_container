#!/bin/bash -ex

if [ -f "/home/travis/build/leukgen/toil_container/singularity/bin/singularity" ]; then
    apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
    git clone https://github.com/singularityware/singularity.git
    cd singularity
    ./autogen.sh
    ./configure --prefix=/home/travis/build/leukgen/toil_container/singularity
    make install
else
    echo exists
fi
