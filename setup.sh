#!/bin/bash

git submodule init;
git submodule update;

cd benchmarks/defects4j;
cpanm --installdeps .;
./init.sh;
cd ../..;

cd benchmarks/gitbug-java;
poetry install --no-root;
poetry run ./gitbug-java setup;

docker pull openjdk:11;
