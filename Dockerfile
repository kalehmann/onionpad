FROM "python:slim"
RUN pip install \
    Adafruit-Blinka \
    adafruit-blinka-displayio \
    adafruit-circuitpython-display-shapes \
    adafruit-circuitpython-macropad \
    black \
    pylint
