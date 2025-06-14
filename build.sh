#!/bin/bash

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r backend/requirements.txt

# Create necessary directories
mkdir -p backend/__pycache__ 