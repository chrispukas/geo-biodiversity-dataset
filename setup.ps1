# Define environment name
$envName = "gbio_env"

# Get Conda base path and load Conda functions
$condaBase = & conda info --base
. "$condaBase\etc\profile.d\conda.ps1"

# Check if environment exists, otherwise create it
if (-not (conda env list | Select-String $envName)) {
    conda create --name $envName python=3.12 -y
}

# Activate environment
conda activate $envName

# If environment.yml exists, update the environment
if (Test-Path "environment.yml") {
    conda env update --file environment.yml --prune -y
}

# Install uv
conda install uv -y

# Install local package in editable mode
uv pip install -e .