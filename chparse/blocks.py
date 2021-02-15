import re

from chparse.errors import InvalidEventException, InvalidNoteException, InvalidLyricException, InvalidMetadataException, InvalidSyncEventException, InvalidTimeException
from chparse.ini import DataBlockReader


class SongBlock:
    @classmethod
    def parse(cls, f, header):
        datablock = DataBlockReader(f, header)
        if datablock.name == Metadata.HEADER:
            return Metadata.parse(datablock)
        else:
            return Track.parse(datablock)


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


class Track(SongBlock):
    def __init__(self):
        self.items = []

    def append(self, value):
        self.items.append(value)

    @classmethod
    def parse(cls, datablock):
        if datablock.name == SyncTrack.HEADER:
            return SyncTrack.parse(datablock)
        elif datablock.name == EventsTrack.HEADER:
            return EventsTrack.parse(datablock)
        elif datablock.name == LyricsTrack.HEADER:
            return LyricsTrack.parse(datablock)
        else:
            return ChartTrack.parse(datablock)


class SyncTrack(Track):
    HEADER = "SyncTrack"
    RE_SYNC_KIND_VALUE = re.compile(r'^([A-Z]{1,2})\s+([0-9]+)$')

    @classmethod
    def parse(cls, datablock):
        synctrack = cls()
        for time, value in datablock:
            synctrack.append(SyncEvent.parse(time, value))
        return synctrack


class EventsTrack(Track):
    HEADER = "Events"

    @classmethod
    def parse(cls, datablock):
        events = cls()
        for time, value in datablock:
            events.append(Event.parse(time, value))
        return events


class LyricsTrack(Track):
    HEADER = "Lyrics"

    @classmethod
    def parse(cls, datablock):
        lyrics = cls()
        for time, value in datablock:
            time = Time.parse(time)
            event = LyricNote.parse(time, value) or LyricWord.parse(time, value)     # short-circuit evaluation
            if event is None:
                raise InvalidLyricException
            lyrics.append(event)
        return lyrics


class ChartTrack(Track):
    DIFFICULTIES = ("Easy", "Medium", "Hard", "Expert")
    INSTRUMENTS = ("Single", "DoubleGuitar", "DoubleBass", "DoubleRhythm", "Keyboard", "Drums", "GHLGuitar", "GHLBass")
    GHL_INSTRUMENTS = ("GHLGuitar", "GHLBass")

    def __init__(self, difficulty, instrument):
        super().__init__()
        self.difficulty = difficulty
        self.instrument = instrument

    @classmethod
    def parse(cls, datablock):
        difficulty, instrument = cls.parse_header(datablock.name)
        chart = cls(difficulty, instrument)
        for time, value in datablock:
            try:
                event = ChartNote.parse(time, value)
            except InvalidNoteException:
                event = Event.parse(time, value)
            chart.append(event)
        return chart

    @classmethod
    def parse_header(cls, header):
        for d in cls.DIFFICULTIES:
            if header.startswith(d):
                i = header.removeprefix(d)
                if i in cls.INSTRUMENTS:
                    return d, i
        raise InvalidNoteException


class TrackItem:
    def __init__(self, time):
        self.time = time


class GenericEvent(TrackItem):
    RE_EVENT = re.compile(r'^([A-Z]{1,2})\s+(.*)$')

    def __init__(self, time, kind, value):
        super().__init__(time)
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"{self.time} = {self.kind} {self.value!r}"

    @classmethod
    def parse(cls, time, value):
        time = Time.parse(time)
        match = cls.RE_EVENT.match(value)
        if match is None:
            raise InvalidEventException
        kind, value = match.groups()
        return cls(time, kind, value)


class GenericNote(TrackItem):
    RE_NOTE = re.compile(r'^([A-Z])\s+([0-9]+)\s+([0-9]+)$')

    def __init__(self, time, kind, value, length):
        super().__init__(time)
        self.kind = kind
        self.value = value
        self.length = length

    @classmethod
    def parse(cls, time, value):
        match = cls.RE_NOTE.match(value)
        if match is None:
            raise InvalidNoteException
        kind, value, length = match.groups()
        value = int(value)
        length = int(length)
        return cls(time, kind, value, length)

    def __repr__(self):
        return f"{self.time} = {self.kind} {self.value} {self.length}"


class LyricNote(GenericNote):
    def __init__(self, time, kind, value, length):
        if kind not in ("N",):
            raise InvalidSyncEventException
        super().__init__(time, kind, value, length)


class LyricWord(GenericEvent):
    def __init__(self, time, kind, value):
        if kind not in ("E",):
            raise InvalidLyricException
        super().__init__(time, kind, value)


class ChartNote(GenericNote):
    def __init__(self, time, kind, value, length):
        if kind not in ("N", "S"):
            raise InvalidNoteException
        super().__init__(time, kind, value, length)


class Event(GenericEvent):
    def __init__(self, time, kind, value):
        if kind not in ("E",):
            raise InvalidEventException
        value = value.strip('"')
        super().__init__(time, kind, value)


class SyncEvent(GenericEvent):
    def __init__(self, time, kind, value):
        if kind not in ("A", "B", "TS"):
            raise InvalidSyncEventException
        try:
            value = int(value)
        except ValueError:
            raise InvalidSyncEventException
        super().__init__(time, kind, value)


class Time:
    @staticmethod
    def parse(s):
        if not s.isdigit():
            raise InvalidTimeException
        time = int(s)
        return time
