#!/bin/sh
# Update pip and install LEAP base requirements.
# For convenience, u1db and dirspec are allowed with insecure flags enabled.
# Use at your own risk.
pip install -U pip
pip install --allow-external dirspec --allow-unverified dirspec -r pkg/requirements.pip
