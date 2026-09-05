#!/usr/bin/env bash

if [ -d "dist" ]; then
    rm -rf dist
fi

mkdir dist

uvx shiv -o dist/visualizer.pyz --site-packages=.venv/lib/python3.14/site-packages -e visualizer.main:run  .
if [ ! -L "/usr/local/bin/bopmux-visualizer" ]; then
    ln -s $PWD/dist/visualizer.pyz /usr/local/bin/bopmux-visualizer
fi

uvx shiv -o dist/runner.pyz --site-packages=.venv/lib/python3.14/site-packages -e runner.main:run  .
if [ ! -L "/usr/local/bin/bopmux-visualizer" ]; then
    ln -s $PWD/dist/visualizer.pyz /usr/local/bin/bopmux-visualizer
fi
