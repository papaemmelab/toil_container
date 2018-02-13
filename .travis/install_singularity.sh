#!/bin/bash -ex

if [ -f "/home/travis/build/leukgen/toil_container/singularity/bin/singularity" ]; then
    echo exists
else
    rm -rf /home/travis/build/leukgen/toil_container/singularity
    apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
    git clone https://github.com/singularityware/singularity.git
    cd singularity
    ./autogen.sh
    ./configure --prefix=/home/travis/build/leukgen/toil_container/singularity
    make install
fi
