#!/bin/bash

git submodule init;
git submodule update;

cd ../../defects4j;
cpanm --installdeps .;
./init.sh;
cd ../../../;