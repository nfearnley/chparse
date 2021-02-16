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


class InvalidNumberException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid number", *args, **kwargs)


class InvalidTimeException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid time", *args, **kwargs)


class InvalidTrackHeaderException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid track header", *args, **kwargs)


class InvalidTrackItemException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid track item", *args, **kwargs)


class InvalidMetadataException(SongFileException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid metadata", *args, **kwargs)
