from itertools import product
import re

from chparse.errors import InvalidMetadataException, InvalidNumberException, InvalidTimeException, InvalidTrackHeaderException, InvalidTrackItemException
from chparse.datablock import DataBlockReader


# Songblocks

class SongBlock:
    @classmethod
    def parse(cls, f, header):
        datablock = DataBlockReader(f, header)
        if datablock.name == Metadata.HEADER:
            return Metadata.parse(datablock)
        else:
            return Track.parse(datablock)


# Metadata

class Metadata(SongBlock):
    HEADER = "Song"
    RE_METADATA_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')

    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    @classmethod
    def parse(cls, datablock):
        metadata = cls()
        for name, value in datablock:
            if not cls.RE_METADATA_NAME.match(name):
                raise InvalidMetadataException
            try:
                value = int(value)
            except ValueError:
                value = value.strip('"')
            metadata[name] = value
        return metadata


# Tracks

class Track(SongBlock):
    HEADER = None
    HEADERS = []

    def __init__(self, header, items):
        self.items = items

    @classmethod
    def parse(cls, datablock):
        header = datablock.name
        try:
            subcls = next(t for t in cls.__subclasses__() if header in (t.HEADERS + [t.HEADER]))
        except StopIteration:
            raise InvalidTrackHeaderException
        items = []
        for time, rest in datablock:
            time = parse_time(time)
            item = TrackItem.parse(time, rest)
            items.append(item)
        track = subcls(header, items)
        return track


class SyncTrack(Track):
    HEADER = "SyncTrack"


class EventsTrack(Track):
    HEADER = "Events"


class LyricsTrack(Track):
    HEADER = "PART VOCALS"


class ChartTrack(Track):
    DIFFICULTIES = ("Easy", "Medium", "Hard", "Expert")
    INSTRUMENTS = ("Single", "DoubleGuitar", "DoubleBass", "DoubleRhythm", "Keyboard", "Drums", "GHLGuitar", "GHLBass")
    HEADER_MAP = {d + i: (d, i) for d, i in product(DIFFICULTIES, INSTRUMENTS)}    # Precalculate all DifficultyInstrument pairings
    HEADERS = list(HEADER_MAP.keys())

    def __init__(self, header, items):
        super().__init__(header, items)
        self.difficulty, self.instrument = self.HEADER_MAP[header]


# Track Items

class TrackItem:
    RE_TRACK_ITEM = re.compile(r'^([A-Z]{1,2})\s+(.*)$')

    def __init__(self, time):
        self.time = time

    @classmethod
    def parse(cls, time, rest):
        match = cls.RE_TRACK_ITEM.match(rest)
        if not match:
            raise InvalidTrackItemException
        kind, rest = match.groups()
        try:
            subcls = next(t for t in cls.__subclasses__() if kind == t.KIND)
        except StopIteration:
            raise InvalidTrackItemException
        return subcls.parse(time, rest)


class TimeSignatureEvent(TrackItem):
    KIND = "TS"

    def __init__(self, time, high, low):
        super().__init__(time)
        self.high = high
        self.low = low

    @classmethod
    def parse(cls, time, rest):
        highlow = parse_nums(rest, 1, 2)
        high = highlow[0]
        try:
            low = highlow[1]
        except IndexError:
            low = 4
        return cls(time, high, low)

    def __repr__(self):
        return f"{self.time} = {self.KIND} {self.high} {self.low}"


class BPMItem(TrackItem):
    KIND = "B"

    def __init__(self, time, mBPM):
        super().__init__(time)
        self.mBPM = mBPM

    @classmethod
    def parse(cls, time, rest):
        mBPM = parse_num(rest)
        return cls(time, mBPM)

    def __repr__(self):
        return f"{self.time} = {self.KIND} {self.mBPM}"


class NoteItem(TrackItem):
    KIND = "N"

    def __init__(self, time, fret, length):
        super().__init__(time)
        self.fret = fret
        self.length = length

    @classmethod
    def parse(cls, time, rest):
        fret, length = parse_nums(rest, 2)
        return cls(time, fret, length)

    def __repr__(self):
        return f"{self.time} = {self.KIND} {self.fret} {self.length}"


class EventItem(TrackItem):
    KIND = "E"

    def __init__(self, time, text):
        super().__init__(time)
        self.text = text

    @classmethod
    def parse(cls, time, rest):
        values = parse_text(rest)
        return cls(time, values)

    def __repr__(self):
        return f"{self.time} = {self.KIND} {self.text!r}"


class AnchorItem(TrackItem):
    KIND = "A"

    def __init__(self, time, mBPM):
        super().__init__(time)
        self.mBPM = mBPM

    @classmethod
    def parse(cls, time, rest):
        mBPM = parse_num(rest)
        return cls(time, mBPM)

    def __repr__(self):
        return f"{self.time} = {self.KIND} {self.mBPM}"


class StarPowerItem(TrackItem):
    KIND = "S"

    def __init__(self, time, akhjfgswder, length):
        super().__init__(time)
        self.akhjfgswder = akhjfgswder
        self.length = length

    @classmethod
    def parse(cls, time, rest):
        akhjfgswder, length = parse_nums(rest, 2)
        return cls(time, akhjfgswder, length)

    def __repr__(self):
        return f"{self.time} = {self.KIND} {self.akhjfgswder} {self.length}"


# Parsing functions

def parse_time(s):
    if not s.isdigit():
        raise InvalidTimeException
    time = int(s)
    return time


def parse_text(s):
    return s.strip('"')


def parse_num(s):
    return parse_nums(s, 1)[0]


def parse_nums(s, min, max=None):
    RE_NUM = re.compile(r'\s*([0-9]+)')
    if max is None:
        max = min
    try:
        values = [int(v) for v in RE_NUM.findall(s)]
    except ValueError:
        raise InvalidNumberException
    if not (min <= len(values) <= max):
        raise InvalidNumberException
    return values
