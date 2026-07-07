#!/bin/sh

rm dist/*
uv build --all-packages
uv publish

