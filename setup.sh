#!/bin/bash

Setup submodules
git submodule init;
git submodule update;

cd benchmarks/defects4j;
cpanm --installdeps .;
./init.sh;
cd ../..;

# Setup GHRB
cd benchmarks/GHRB;
cd Docker;
docker build -t ghrb_framework --load .;
docker ps -aq --filter "name=ghrb_framework" | grep -q . && docker stop ghrb_framework && docker rm ghrb_framework;
cd ..;
docker run -dt --name ghrb_framework -v $(pwd):/root/framework ghrb_framework:latest;
docker exec --workdir /root/framework/ ghrb_framework bash -c "chmod +x cli.py";
docker exec --workdir /root/framework/debug/ ghrb_framework bash -c "python3.9 collector.py";