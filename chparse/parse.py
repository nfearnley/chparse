from chparse.rawclasses import Metadata, SongBlock
import sys

"""Parse (or unparse) a file to/from a Song object!"""
from chparse.errors import DataBlockException
import re
from .song import Song

RE_DIFFICULTY_KIND = re.compile(r'^([A-Z][a-z]+)([A-Z][A-Za-z]+)$')
RE_NOTE = re.compile(r'^([NS])\s+([0-9]+)\s+([0-9]+)$')
RE_NOTE_EVENT = re.compile(r'^E\s+"?([a-zA-Z\*]+)"?$')


class ParseError(Exception):
    """The chart is invalid."""
    pass


class FileCounter:
    def __init__(self, f):
        try:
            readline = f.readline
        except AttributeError:
            readline = None
        if readline is None or not callable(readline):
            raise TypeError("f must be a file object (or something with a \"readline\" method)")
        self._readline = readline
        self.lineno = -1
        self.line = None

    def readline(self):
        self.lineno += 1
        self.line = self._readline()
        return self.line


def load(f):
    """Load a chart from a file object."""
    f = FileCounter(f)
    chart = None
    tracks = []
    # replaced broken EOF code with a walrus operator
    while line := f.readline():
        line = line.strip().strip('\ufeff').strip("ï»¿")
        # ignore blank lines
        if not line:
            continue
        # ignore lines that don't start with '['
        if not line.startswith('['):
            continue
        try:
            block = SongBlock.parse(f, line)
        except DataBlockException as e:
            raise type(e)(lineno=f.lineno, line=f.line).with_traceback(sys.exc_info()[2])
        # if section is a dict, then it's [Song] metadata
        if isinstance(block, Metadata):
            chart = Song(block)
        else:
            tracks.append(block)
    if chart is None:
        raise ValueError("[Song] section not found")
    # Add all the sections found to the chart
    chart.add_tracks(tracks)
    return chart


def dump(chart, fileobj):
    """Dump a Chart to a file (or other object with a write() method)."""
    chart.dump(fileobj)
