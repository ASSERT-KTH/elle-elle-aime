#!/bin/bash

git submodule init;
git submodule update;

cd benchmarks/gitbug-java;
chmod +x gitbug-java;
poetry install --no-root;
# Skip setup if in CI
if [ -z "$CI" ]; then
  poetry run ./gitbug-java setup;
fi

docker pull openjdk:11;
docker pull maven:3.9.8-eclipse-temurin-8;
docker pull andre15silva/defects4j:latest;