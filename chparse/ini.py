import re

RE_DATABLOCK_HEADER = re.compile(r'^\s*\[([A-Za-z ]+)\]\s*$')
RE_DATABLOCK_LINE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.*[^\s])\s*$')


class DataBlockException(Exception):
    def __init__(self, m, lineno=None, line=None):
        self.lineno = lineno
        self.line = line
        if  lineno is not None and line is not None:
            m = f"{m} (line {lineno}: {line!r})"
        super().__init__(m)


class InvalidDataBlockHeaderException(DataBlockException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid data block header", *args, **kwargs)


class InvalidDataBlockLineException(DataBlockException):
    def __init__(self, *args, **kwargs):
        super().__init__("Invalid data block line", *args, **kwargs)


class DataBlockReader:
    def __init__(self, f, line):
        match = RE_DATABLOCK_HEADER.match(line)
        if match is None:
            raise InvalidDataBlockHeaderException()
        self.name = match.group(1)
        self.f = f
        self.done = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.done:
            raise StopIteration
        while True:
            # Read a line from file, stripping it of whitespace
            line = self.f.readline().strip()
            # Ignore open brackets
            if line == "{":
                continue
            # Stop looping after a closing bracket
            if line == "}":
                self.done = True
                raise StopIteration
            match = RE_DATABLOCK_LINE.match(line)
            if match is None:
                raise InvalidDataBlockLineException()
            k, v = match.groups()
            return k, v
