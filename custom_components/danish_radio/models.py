"""Shared models for Danish Radio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NowPlayingData:
    """Normalized now-playing payload."""

    state: str
    station: str
    program: str = ""
    program_start: str = ""
    program_end: str = ""
    program_slug: str = ""
    program_description: str = ""
    artist: str = ""
    title: str = ""
    stream_title: str = ""
    raw_metadata: str = ""
    stream_url: str = ""
    image: str = ""
    source: str = ""
    updated_at: str = ""

    def attributes(self) -> dict[str, str]:
        """Return Home Assistant attributes."""
        return {
            "station": self.station,
            "program": self.program,
            "program_start": self.program_start,
            "program_end": self.program_end,
            "program_slug": self.program_slug,
            "program_description": self.program_description,
            "artist": self.artist,
            "title": self.title,
            "stream_title": self.stream_title,
            "raw_metadata": self.raw_metadata,
            "stream_url": self.stream_url,
            "image": self.image,
            "source": self.source,
            "updated_at": self.updated_at,
        }
