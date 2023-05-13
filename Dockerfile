FROM "gcc:bookworm" AS mpycross
RUN git clone https://github.com/adafruit/circuitpython.git \
    && cd circuitpython \
    && make fetch-submodules \
    && make -C mpy-cross -f Makefile.static \
    && cp mpy-cross/mpy-cross.static /usr/bin/mpy-cross

FROM "python:slim"
ARG UID=1000
ARG GID=1000

RUN mkdir /app
WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y make \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip \
    && pip install \
        Adafruit-Blinka \
        adafruit-blinka-displayio \
        adafruit-circuitpython-display-shapes \
        adafruit-circuitpython-macropad \
        black \
        circuitpython-stubs \
        mypy \
        pylint \
        sphinx \
        sphinx-rtd-theme \
    && pip cache purge

COPY --from=mpycross /usr/bin/mpy-cross /usr/bin/mpy-cross
USER ${UID}:${GID}
