#!/bin/bash

git submodule init;
git submodule update;

cd benchmarks/defects4j;
cpanm --installdeps .;
./init.sh;