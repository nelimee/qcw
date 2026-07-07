#!/bin/sh

rm dist/*
uv build --all-packages
python -m twine upload --repository pypi dist/*

