"""Contains the Instrument class."""
from .note import Note, Event, SyncEvent
from . import flags


class Track(list):
    def __init__(self, kind=None):
        super().__init__()
        if kind is not None:
            self.kind = kind

    @classmethod
    def _check_event(cls, event, kind=(), types=()):
        if not types:
            raise NotImplementedError
        if not isinstance(event, types):
            raise TypeError(f'Expected ({", ".join(str(t) for t in types)}), got {type(event).__name__}')
        if kind != () and event.kind not in kind:
            raise TypeError(f'Expected Event of type {kind.value} but got {event.kind.value}')

    def append(self, event, kind=()):
        self._check_event(event, kind)
        super().append(event)

    def add(self, event, kind=()):
        """Add a event to this track.
        It will be automatically inserted in the correct position.
        """
        self.append(event, kind)
        self.sort()


class Lyrics(Track):
    def __init__(self, kind=None):
        if kind is not None and not isinstance(kind, flags.Metadata):
            raise TypeError(f'Expected a metadata enum, got {type(kind).__name__}')
        super().__init__(kind)

    @classmethod
    def _check_event(cls, event, kind=()):
        return super()._check_event(event, kind, types=(Event, Note))


class Metadata(Track):
    def __init__(self, kind=None):
        if kind is not None and not isinstance(kind, flags.Metadata):
            raise TypeError(f'Expected a metadata enum, got {type(kind).__name__}')
        super().__init__(kind)

    def __str__(self):
        if self.kind == flags.EVENTS:
            result = '[' + self.kind.value + ']\n{\n'
            for note in self:
                result += str(note) + '\n'
            result += '}'
            return result

    @classmethod
    def _check_event(cls, event, kind=()):
        return super()._check_event(event, kind, types=(Event, SyncEvent))


class Instrument(Track):
    """Represents a single track (e.g. ExpertSingle)."""
    difficulty = flags.EXPERT
    kind = flags.GUITAR

    def __init__(self, kind=None, difficulty=None, notes=None):
        if kind is not None and not isinstance(kind, flags.Instruments):
            raise TypeError(f'Expected a instrument enum, got {type(kind).__name__}')
        super().__init__(kind)
        if difficulty is not None:
            if not isinstance(difficulty, flags.Difficulties):
                raise TypeError(f'Expected a difficulty enum, got {type(difficulty).__name__}')
            self.difficulty = difficulty
        if notes is not None:
            try:
                self.extend(notes)
            except TypeError:
                raise TypeError(f'expected iterable notes list, got {type(notes).__name__}') from None

    def __repr__(self):
        first_notes = list(self[:5])
        return '<Instrument, first notes: {}>'.format(
            repr(first_notes)
        )

    def __str__(self):
        result = '['
        result += self.difficulty.value or ''
        result += self.kind.value
        result += ']\n{\n'
        for note in self:
            result += str(note) + '\n'
        result += '}'
        return result

    @classmethod
    def _check_event(cls, event, kind=()):
        return super()._check_event(event, kind, types=(Note, Event))
