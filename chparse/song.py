class Song:
    """Represents an entire Song."""

    def __init__(self, metadata):
        self.__dict__.update(metadata.data)
        self.tracks = []

    def add_track(self, track):
        self.tracks.append(track)

    def add_tracks(self, tracks):
        self.tracks.extend(tracks)
