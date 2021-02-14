"""Parse (or unparse) a file to/from a Chart object!"""
import re
from .note import Note, Event, SyncEvent
from .instrument import Instrument, Metadata, Lyrics
from .chart import Chart
from . import flags

RE_SECTION_HEADER = re.compile(r'\[([A-Za-z ]+)\]')
RE_NAME_VALUE = re.compile(r'([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*)')
RE_DIFFICULTY_KIND = re.compile(r'([A-Z][a-z]+)([A-Z][A-Za-z]+)')
RE_NOTE = re.compile(r'([0-9]+)\s*=\s*([A-Z])\s+([0-9]+)\s+([0-9]+)')
RE_EVENT = re.compile(r'([0-9]+)\s*=\s*(E)\s+"?([a-zA-Z\*]+)"?')
RE_LYRIC_WORD = re.compile(r'([0-9]+)\s*=\s*(E)\s+"?([a-zA-Z\-#.!]+)"?')


class ParseError(Exception):
    """The chart is invalid."""
    pass


def load(fileobj):
    """Load a chart from a file object."""
    if not hasattr(fileobj, 'readline'):
        raise TypeError('fileobj must be a file object (or something with a "readline" method)')
    chart = None
    sections = []
    # replaced broken EOF code with a walrus operator
    while line := fileobj.readline():
        line = line.strip().strip('\ufeff').strip("ï»¿")
        # ignore blank lines
        if not line:
            continue
        # ignore lines that don't start with '['
        if not line.startswith('['):
            continue
        section = _parse_section(fileobj, line)
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


def _parse_section(fileobj, section_header):
    try:
        section_name = RE_SECTION_HEADER.match(section_header).group(1)
        meta_flag = flags.Metadata(section_name)
    except ValueError:
        meta_flag = None
    if meta_flag is None:
        return _parse_inst(fileobj, section_header)
    if meta_flag == flags.SONG:
        return _parse_song(fileobj)
    if meta_flag == flags.SYNC:
        return _parse_sync(fileobj)
    if meta_flag == flags.EVENTS:
        return _parse_events(fileobj)
    if meta_flag == flags.LYRICS:
        return _parse_lyrics(fileobj)
    raise ValueError(f"Unprocessable section: {section_header}")


def _parse_song(fileobj):
    data = {}
    for line in _section_lines(fileobj):
        # Get "name = value" pair name
        name, value = RE_NAME_VALUE.search(line).groups()
        # Try to parse as int, or strip quotes
        try:
            value = int(value)
        except ValueError:
            value = value.strip('"')
        data[name] = value
    return data


def _parse_sync(fileobj):
    inst = Metadata(kind=flags.SYNC)
    for line in _section_lines(fileobj):
        time, kind, value = re.search(r'([0-9]+)\s*=\s*([A-Z]{1,2})\s+([0-9]+)', line).groups()
        time = int(time)
        kind = flags.NoteTypes(kind)
        value = int(value)
        inst.append(SyncEvent(time, kind, value))
        inst.sort()
    return inst


def _parse_events(fileobj):
    inst = Metadata(kind=flags.EVENTS)
    for line in _section_lines(fileobj):
        match = re.search(r'([0-9]+)\s*=\s*' + flags.EVENT.value + r'\s+("?.*"?)', line)
        time = int(match.group(1))
        evt = match.group(2).strip('"')
        inst.append(Event(time, evt))
        inst.sort()     # just in case
    return inst


def _parse_lyrics(fileobj):
    lyrics = Lyrics(kind=flags.LYRICS)
    for line in _section_lines(fileobj):
        event = _parse_lyric_note(line) or _parse_lyric_word(line)     # short-circuit evaluation
        if event is None:
            raise ValueError(f"Bad section line: {line}")
        lyrics.append(event)
    return lyrics


# Generator to easily parse section lines
def _section_lines(fileobj):
    while True:
        # Read a line from file, stripping it of whitespace
        line = fileobj.readline().strip()
        # Ignore open brackets
        if line == "{":
            continue
        # Stop looping after a closing bracket
        if line == "}":
            break
        yield line


def _parse_inst(fileobj, section_header):
    section_name = RE_SECTION_HEADER.match(section_header).group(1)
    difficulty, kind = RE_DIFFICULTY_KIND.match(section_name).groups()
    inst = Instrument(
        kind=flags.Instruments(kind),
        difficulty=flags.Difficulties(difficulty)
    )
    islive = kind in (flags.GHL_GUITAR, flags.GHL_BASS)

    for line in _section_lines(fileobj):
        note = _parse_note(line, islive)
        if note is None:
            event = _parse_event(line)
            inst.append(event)
        elif isinstance(note, set):
            extraflags = note
            inst[-1].flags |= extraflags
        elif isinstance(note, Note):
            inst.append(note)
        else:
            raise ValueError(f"Bad section line: {line}")

    return inst


def _parse_lyric_note(line):
    match = RE_NOTE.match(line)
    if match is None:
        return None
    time, kind, fret, length = match.groups()
    return Note(time, kind=flags.NoteTypes(kind), fret=fret, length=length)


def _parse_lyric_word(line):
    match = RE_LYRIC_WORD.match(line)
    if match is None:
        return None
    time, kind, evt = match.groups()
    return Event(time, evt)


def _parse_note(line, islive=False):
    match = RE_NOTE.match(line)
    if match is None:
        return None
    time, kind, raw_fret, length = match.groups()
    time = int(time)
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


def _parse_event(line):
    match = RE_EVENT.search(line)
    if not match:
        raise ValueError("Invalid Event: {line}")
    time, kind, evt = match.groups()
    return Event(int(time), evt.strip('"'))


def dump(chart, fileobj):
    """Dump a Chart to a file (or other object with a write() method)."""
    chart.dump(fileobj)
