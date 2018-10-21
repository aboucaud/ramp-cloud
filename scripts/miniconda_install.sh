#!/bin/bash
#
# Setup up miniconda on a machine

set -e
set -x

LATEST_MINICONDA="http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh"

# Download into home
wget -q $LATEST_MINICONDA -O $HOME/miniconda.sh

# Exectute installation without prompt
bash $HOME/miniconda.sh -b -p $HOME/miniconda3

# Add to the path
echo 'export PATH="${HOME}/miniconda3/bin:$PATH"' >> $HOME/.profile
source $HOME/.profile

# Perform updates
conda update --yes --quiet conda
pip install --upgrade pip

# Update conda with RAMP specific dependencies
conda env update --name base --file $ENV_FILE

# Update conda with the kit specific dependencies
ami_environment="$HOME/ramp-kits/$KIT_NAME/ami_environment.yml"
conda env update --name base --file $ami_environment
