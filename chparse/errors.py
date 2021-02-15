class DataBlockException(Exception):
    def __init__(self, m, lineno=None, line=None):
        self.lineno = lineno
        self.line = line
        if lineno is not None and line is not None:
            m = f"{m} (line {lineno}: {line!r})"
        super().__init__(m)


class InvalidDataBlockHeaderException(DataBlockException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid data block header", *args, **kwargs)


class InvalidDataBlockLineException(DataBlockException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid data block line", *args, **kwargs)


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


class InvalidNoteException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid instrument", *args, **kwargs)
