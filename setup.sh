#!/usr/bin/env bash
ENV_NAME="gbio_env"

# Install conda dependencies
source "$(conda info --base)/etc/profile.d/conda.sh"

conda env list | grep -q "$ENV_NAME\s" || conda create --name $ENV_NAME python=3.12 -y
conda activate $ENV_NAME

if [ -f "environment.yml" ]; then
    conda env update --file environment.yml --prune -y
fi

conda install uv

# Install local package
uv pip install -e.