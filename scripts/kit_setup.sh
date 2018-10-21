#!/bin/bash
#
# Setup a RAMP backend architecture for a given RAMP project

set -e
set -x

kit_url="https://github.com/ramp-kits/$KIT_NAME"
kit_dir="$HOME/ramp-kits/$KIT_NAME"
data_dir="$kit_dir/data"

# Prepare directory for ramp kit
mkdir $HOME/ramp-kits

# Clone the kit
git clone $kit_url $kit_dir

# Prepare the data directory for backend data upload
rm -rf $data_dir && mkdir $data_dir
