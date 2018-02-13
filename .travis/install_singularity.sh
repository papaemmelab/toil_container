#!/bin/bash -ex

# if [ -f "$HOME/singularity/bin/singularity" ]; then
#     echo exists
# else
apt-get update && apt-get install squashfs-tools dh-autoreconf build-essential
git clone https://github.com/singularityware/singularity.git
cd singularity
./autogen.sh
./configure --prefix=$HOME/singularity
make install
# fi
