FROM "python:slim"
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install make \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    Adafruit-Blinka \
    adafruit-blinka-displayio \
    adafruit-circuitpython-display-shapes \
    adafruit-circuitpython-macropad \
    black \
    pylint \
    sphinx \
    sphinx-rtd-theme \
    && pip cache purge

