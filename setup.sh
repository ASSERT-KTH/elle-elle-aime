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
# Skip setup if in CI
if [ -z "$CI" ]; then
  poetry run ./gitbug-java setup;
fi

docker pull openjdk:11;
