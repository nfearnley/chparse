import sys

"""Parse (or unparse) a file to/from a Chart object!"""
from chparse.ini import DataBlockReader, DataBlockException
import re
from .note import Note, Event, SyncEvent
from .instrument import Instrument, Metadata, Lyrics
from .chart import Chart
from . import flags

RE_TIME = re.compile(r'^[0-9]+$')
RE_METADATA_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
RE_SYNC_KIND_VALUE = re.compile(r'^([A-Z]{1,2})\s+([0-9]+)$')
RE_EVENT = re.compile(r'^E\s+(.*)$')

RE_DIFFICULTY_KIND = re.compile(r'^([A-Z][a-z]+)([A-Z][A-Za-z]+)$')
RE_NOTE = re.compile(r'^([NS])\s+([0-9]+)\s+([0-9]+)$')
RE_NOTE_EVENT = re.compile(r'^E\s+"?([a-zA-Z\*]+)"?$')
RE_LYRIC_WORD = re.compile(r'^E\s+"?([a-zA-Z\-#.!]+)"?$')


class SongFileException(DataBlockException):
    pass


class InvalidTimeException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid metadata", *args, **kwargs)


class InvalidMetadataException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid metadata", *args, **kwargs)


class InvalidSyncEventException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid sync event", *args, **kwargs)


class InvalidEventException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid event", *args, **kwargs)


class InvalidLyricException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid lyric", *args, **kwargs)


class InvalidInstrumentException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid instrument", *args, **kwargs)


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
    sections = []
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
            section = _parse_datablock(f, line)
        except DataBlockException as e:
            raise type(e)(lineno=f.lineno, line=f.line).with_traceback(sys.exc_info()[2])
        # if section is a dict, then it's [Song] metadata
        if isinstance(section, dict):
            chart = Chart(section)
        else:
            sections.append(section)
    if chart is None:
        raise ValueError("[Song] section not found")
    # Add all the sections found to the chart
    for i in sections:
        chart.add(i)
    return chart


def _parse_datablock(fileobj, datablock_header):
    datablock = DataBlockReader(fileobj, datablock_header)
    try:
        meta_flag = flags.Metadata(datablock.name)
    except ValueError:
        meta_flag = None
    if meta_flag is None:
        return _parse_inst(datablock)
    if meta_flag == flags.SONG:
        return _parse_metadata(datablock)
    if meta_flag == flags.SYNC:
        return _parse_sync(datablock)
    if meta_flag == flags.EVENTS:
        return _parse_events(datablock)
    if meta_flag == flags.LYRICS:
        return _parse_lyrics(datablock)
    raise ValueError(f"Unprocessable section: {datablock_header}")


def _parse_metadata(datablock):
    data = {}
    for name, value in datablock:
        if not RE_METADATA_NAME.match(name):
            raise InvalidMetadataException()
        try:
            value = int(value)
        except ValueError:
            value = value.strip('"')
        data[name] = value
    return data


def _parse_sync(datablock):
    inst = Metadata(kind=flags.SYNC)
    for time, value in datablock:
        time = _parse_time(time)
        match = RE_SYNC_KIND_VALUE.match(value)
        if match is None:
            raise InvalidSyncEventException()
        kind, value = match.groups()
        if kind not in ["A", "B", "TS"]:
            raise InvalidSyncEventException()
        time = int(time)
        kind = flags.NoteTypes(kind)
        value = int(value)
        inst.append(SyncEvent(time, kind, value), sort=True)
    return inst


def _parse_events(datablock):
    inst = Metadata(kind=flags.EVENTS)
    for time, value in datablock:
        time = _parse_time(time)
        match = RE_EVENT.match(value)
        if match is None:
            raise InvalidEventException()
        evt = match.group(1).strip('"')
        inst.append(Event(time, evt), sort=True)
    return inst


def _parse_lyrics(datablock):
    lyrics = Lyrics(kind=flags.LYRICS)
    for time, value in datablock:
        time = _parse_time(time)
        event = _parse_lyric_note(time, value) or _parse_lyric_word(value)     # short-circuit evaluation
        if event is None:
            raise InvalidLyricException()
        lyrics.append(event)
    return lyrics


def _parse_lyric_note(time, line):
    match = RE_NOTE.match(line)
    if match is None:
        return None
    fret, length = match.groups()
    return Note(time, kind=flags.NOTE, fret=fret, length=length)


def _parse_lyric_word(time, line):
    match = RE_LYRIC_WORD.match(line)
    if match is None:
        return None
    evt = match.groups()
    return Event(time, evt)


def _parse_inst(datablock):
    difficulty, kind = RE_DIFFICULTY_KIND.match(datablock.name).groups()
    try:
        inst = Instrument(
            kind=flags.Instruments(kind),
            difficulty=flags.Difficulties(difficulty)
        )
    except ValueError:
        raise InvalidInstrumentException()
    islive = kind in (flags.GHL_GUITAR, flags.GHL_BASS)

    for time, value in datablock:
        event = _parse_note(time, value, islive) or _parse_event(time, value)
        if event is None:
            raise InvalidInstrumentException()
        if isinstance(event, set):
            inst[-1].flags |= event
        else:
            inst.append(event)

    return inst


def _parse_note(time, value, islive=False):
    match = RE_NOTE.match(value)
    if match is None:
        return None
    kind, raw_fret, length = match.groups()
    raw_fret = int(raw_fret)
    length = int(length)
    extraflags = set()
    max_fret = 4

    if islive:
        max_fret = 5
        extraflags.add(flags.GHLIVE)
    # open fret is remapped to fret 0, with OPEN flag
    if flags.Flags(raw_fret) == flags.OPEN:
        extraflags.add(flags.OPEN)
        raw_fret = 0

    # Out of range frets are flags
    if raw_fret > max_fret:
        extraflags.add(flags.Flags(raw_fret))
        return extraflags

    return Note(time, kind=flags.NoteTypes(kind), fret=raw_fret, length=length, flags=extraflags)


def _parse_event(time, line):
    match = RE_NOTE_EVENT.search(line)
    if not match:
        return None
    evt = match.group(1).strip('"')
    return Event(time, evt)


def dump(chart, fileobj):
    """Dump a Chart to a file (or other object with a write() method)."""
    chart.dump(fileobj)


def _parse_time(time):
    if not time.isnumeric():
        raise InvalidTimeException()
    return int(time)
