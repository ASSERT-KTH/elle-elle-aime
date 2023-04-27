FROM archlinux:base-devel

# Setup dependencies
RUN pacman -Syu --noconfirm
RUN pacman -Sy --noconfirm git subversion jdk8-openjdk curl unzip cpanminus python python-distutils-extra python-poetry
RUN archlinux-java set java-8-openjdk
ENV PATH /usr/bin/vendor_perl:/usr/bin/core_perl:$PATH
RUN pacman -Scc --noconfirm

# Setup environment
WORKDIR /llm-repair-them-all/
ENV WORKDIR /llm-repair-them-all/

# Setup plm-repair-them-all
RUN mkdir ./repair
RUN mkdir ./output
COPY benchmarks ./benchmarks
COPY data ./data
COPY src ./src
COPY resources ./resources
COPY .env.docker ./.env
COPY .git ./.git
COPY .gitmodules ./.gitmodules
COPY README.md ./README.md
COPY pyproject.toml ./pyproject.toml
COPY setup.sh ./setup.sh
RUN ./setup.sh

# Install Defects4J
RUN cd ./benchmarks/defects4j && cpanm --installdeps . && ./init.sh
ENV PATH $WORKDIR/benchmarks/defects4j/framework/bin:$PATH

# Install Poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

ENTRYPOINT ["/bin/bash"]