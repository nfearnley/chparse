from chparse.errors import InvalidDataBlockHeaderException, InvalidDataBlockLineException
import re

RE_DATABLOCK_HEADER = re.compile(r'^\s*\[([A-Za-z ]+)\]\s*$')
RE_DATABLOCK_LINE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.*[^\s])\s*$')


class DataBlockReader:
    def __init__(self, f, line):
        match = RE_DATABLOCK_HEADER.match(line)
        if match is None:
            raise InvalidDataBlockHeaderException
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
                raise InvalidDataBlockLineException
            k, v = match.groups()
            return k, v
