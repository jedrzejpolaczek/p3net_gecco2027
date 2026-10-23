# Level-2 reference for MO-DSA (v005-level2-criteria.md): SAGOMEA, github.com/ArkadiyD/SAGOMEA @ 12d67ba (GPL-2),
# cloned next to this file as ./SAGOMEA, unchanged; trap_fitness.py adds the test objective (README: custom function).
#   docker build -t p3net-sagomea:1 .
FROM python:3.6-slim-buster
RUN echo "deb http://archive.debian.org/debian buster main" > /etc/apt/sources.list \
    && echo "deb http://archive.debian.org/debian-security buster/updates main" >> /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends g++ make swig \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy==1.19.5 scipy==1.5.4 scikit-learn==0.24.1 catboost==0.24.2 openml==0.11.0 \
    && pip install --no-cache-dir pyrfr==0.8.0 \
    && pip install --no-cache-dir torch==1.8.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
COPY SAGOMEA /sagomea
COPY trap_fitness.py /tmp/trap_fitness.py
RUN cat /tmp/trap_fitness.py >> /sagomea/py_src/fitnessFunctions.py
WORKDIR /sagomea
RUN mkdir -p build_SAGOMEA && make -f Makefile_SAGOMEA \
      LIBFLAGS="-lstdc++fs -I/usr/local/include/python3.6m -L/usr/local/lib -lpython3.6m"
ENV LD_LIBRARY_PATH=/usr/local/lib
