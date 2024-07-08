#!/bin/bash

git submodule init;
git submodule update;

cd benchmarks/defects4j;
cpanm --installdeps .;
./init.sh;
cd ../..;

cd benchmarks/gitbug-java;
chmod +x gitbug-java;
poetry install --no-root;

docker pull openjdk:11;
