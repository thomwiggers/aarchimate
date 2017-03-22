#!/bin/sh
mypy --strict library.py
flake8 library.py
