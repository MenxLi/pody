#!/bin/bash
set -e
npm run docs:build 
if [ -d "pody/doc" ] && [ "$(ls pody/doc)" ]; then
    echo "pody/doc is not empty, removing contents..."
    rm -r pody/doc/* && touch pody/doc/.gitkeep 
fi
cp -r docs/.vitepress/dist/* pody/doc/
echo "Documentation built and copied to pody/doc successfully."