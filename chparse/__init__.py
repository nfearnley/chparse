"""
chparse - Parse Clone Hero charts with ease!

Installation
============

Install the stable build via::

    pip install chparse

Or install the latest development (unstable) build via::

    git clone https://github.com/nfearnley/chparse.git
    cd chparse
    python setup.py install

Example Usage
=============

Assuming your .chart file is named "notes.chart"...

.. code-block:: python

    >>> import chparse
    >>> with open('notes.chart') as chartfile:
    ...     chart = chparse.load(chartfile)
    >>> chart.instruments[chparse.EXPERT][chparse.GUITAR][0]
    <Note: 0 = N 3 0 (<Flags.NONE: 0>)>
"""
from .parse import load   # noqa: F401

__version__ = "0.0.5"
