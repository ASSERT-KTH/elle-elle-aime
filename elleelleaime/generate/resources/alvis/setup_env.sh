#!/usr/bin/env bash

# Load modules
source load_modules.sh

# Init venv if not already done
if [ ! -d .venv ]; then
    virtualenv --system-site-packages .venv
fi

# Load venv
source .venv/bin/activate

# Install requirements
pip install --no-cache-dir --no-build-isolation -r requirements.txt