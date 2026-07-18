"""Built-in Danish radio station catalog."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .const import (
    CONF_NAME,
    CONF_PROVIDER,
    CONF_RAYO_SLUG,
    CONF_SCHEDULE_SLUG,
    CONF_STATION_ID,
    CONF_STREAM_URL,
    DEFAULT_DR_API_KEY,
    PROVIDER_BAUER_RAYO,
    PROVIDER_DR,
)


def dr_station(station_id: str, name: str, schedule_slug: str) -> dict[str, Any]:
    """Create a DR catalog entry."""
    return {
        CONF_STATION_ID: station_id,
        CONF_NAME: name,
        CONF_PROVIDER: PROVIDER_DR,
        CONF_SCHEDULE_SLUG: schedule_slug,
        "dr_api_key": DEFAULT_DR_API_KEY,
    }


def bauer_station(
    station_id: str,
    name: str,
    rayo_slug: str,
    stream_url: str | None = None,
) -> dict[str, Any]:
    """Create a Bauer/Rayo catalog entry."""
    station = {
        CONF_STATION_ID: station_id,
        CONF_NAME: name,
        CONF_PROVIDER: PROVIDER_BAUER_RAYO,
        CONF_RAYO_SLUG: rayo_slug,
    }
    if stream_url:
        station[CONF_STREAM_URL] = stream_url
    return station


STATIONS: dict[str, dict[str, Any]] = {
    "dr_p1": dr_station("dr_p1", "DR P1", "p1"),
    "dr_p2": dr_station("dr_p2", "DR P2", "p2"),
    "dr_p3": dr_station("dr_p3", "DR P3", "p3"),
    "dr_p4_bornholm": dr_station("dr_p4_bornholm", "DR P4 Bornholm", "p4bornholm"),
    "dr_p4_esbjerg": dr_station("dr_p4_esbjerg", "DR P4 Esbjerg", "p4esbjerg"),
    "dr_p4_fyn": dr_station("dr_p4_fyn", "DR P4 Fyn", "p4fyn"),
    "dr_p4_koebenhavn": dr_station("dr_p4_koebenhavn", "DR P4 København", "p4kbh"),
    "dr_p4_midt_vest": dr_station("dr_p4_midt_vest", "DR P4 Midt & Vest", "p4vest"),
    "dr_p4_nordjylland": dr_station("dr_p4_nordjylland", "DR P4 Nordjylland", "p4nord"),
    "dr_p4_sjaelland": dr_station("dr_p4_sjaelland", "DR P4 Sjælland", "p4sjaelland"),
    "dr_p4_syd": dr_station("dr_p4_syd", "DR P4 Syd", "p4syd"),
    "dr_p4_trekanten": dr_station("dr_p4_trekanten", "DR P4 Trekanten", "p4trekanten"),
    "dr_p4_oestjylland": dr_station("dr_p4_oestjylland", "DR P4 Østjylland", "p4aarhus"),
    "dr_p5_koebenhavn": dr_station("dr_p5_koebenhavn", "DR P5 København", "p5kbh"),
    "dr_p6_beat": dr_station("dr_p6_beat", "DR P6 Beat", "p6beat"),
    "dr_p8_jazz": dr_station("dr_p8_jazz", "DR P8 Jazz", "p8jazz"),
    "nova": bauer_station(
        "nova",
        "NOVA",
        "nova",
        "https://live-bauerdk.sharp-stream.com/nova_dk_mp3?direct=true",
    ),
    "the_voice": bauer_station("the_voice", "The Voice", "the-voice"),
    "radio_100": bauer_station("radio_100", "Radio 100", "radio-100"),
    "pop_fm": bauer_station("pop_fm", "Pop FM", "pop-fm"),
    "radio_soft": bauer_station("radio_soft", "Radio Soft", "radio-soft"),
    "myrock": bauer_station("myrock", "myROCK", "myrock"),
    "radio_klassisk": bauer_station("radio_klassisk", "Radio Klassisk", "radio-klassisk"),
    "radiovinyl": bauer_station("radiovinyl", "Radio Vinyl", "radiovinyl"),
    "mix": bauer_station("mix", "mix", "mix"),
    "nova_top_40": bauer_station("nova_top_40", "NOVA Top 40", "nova-top-40"),
    "nova_100_dansk": bauer_station("nova_100_dansk", "NOVA 100% Dansk", "nova-100-dansk"),
    "go_nova_i_doegndrift": bauer_station(
        "go_nova_i_doegndrift", "Go'Nova i døgndrift", "gonova-i-doegndrift"
    ),
    "nova_sommerhits": bauer_station("nova_sommerhits", "NOVA Sommerhits", "nova-sommerhits"),
    "myrock_legends": bauer_station(
        "myrock_legends", "myROCK Legends of Rock", "myrock-legends-rock"
    ),
    "planet_rock": bauer_station("planet_rock", "Planet Rock", "planet-rock"),
    "radio_soft_classic": bauer_station(
        "radio_soft_classic", "Radio Soft Classic", "radio-soft-classic"
    ),
    "radio_soft_modern": bauer_station(
        "radio_soft_modern", "Radio Soft Modern", "radio-soft-modern"
    ),
    "pop_fm_80er": bauer_station("pop_fm_80er", "Pop FM 80'er", "pop-fm-80er"),
    "pop_fm_90er": bauer_station("pop_fm_90er", "Pop FM 90'er", "pop-fm-90er"),
    "the_voice_in_the_mix": bauer_station(
        "the_voice_in_the_mix", "The Voice In The Mix", "the-voice-in-the-mix"
    ),
    "the_voice_throwback": bauer_station(
        "the_voice_throwback", "The Voice Throwback", "the-voice-throwback"
    ),
    "the_voice_urban": bauer_station("the_voice_urban", "The Voice Urban", "the-voice-urban"),
    "the_voice_k_pop": bauer_station("the_voice_k_pop", "The Voice K-Pop", "the-voice-k-pop"),
    "00s_hits": bauer_station("00s_hits", "00s Hits", "00s-hits"),
    "10s_hits": bauer_station("10s_hits", "10s Hits", "10s-hits"),
    "70er_hits": bauer_station("70er_hits", "70'er Hits", "70er-hits"),
    "80s_hits": bauer_station("80s_hits", "80s Hits", "80s-hits"),
    "90s_hits": bauer_station("90s_hits", "90s Hits", "90s-hits"),
    "danske_80er_hits": bauer_station(
        "danske_80er_hits", "Danske 80'er Hits", "danske-80er-hits"
    ),
    "danske_90er_hits": bauer_station(
        "danske_90er_hits", "Danske 90'er Hits", "danske-90er-hits"
    ),
    "danske_00er_hits": bauer_station(
        "danske_00er_hits", "Danske 00'er Hits", "danske-00er-hits"
    ),
    "ny_dansk_musik": bauer_station("ny_dansk_musik", "Ny Dansk Musik", "ny-dansk-musik"),
    "dansktop_favoritter": bauer_station(
        "dansktop_favoritter", "Dansktop Favoritter", "dansktop-favoritter"
    ),
    "country_classics": bauer_station(
        "country_classics", "Country Classics", "country-classics"
    ),
    "country_modern": bauer_station("country_modern", "Country Modern", "country-modern"),
    "rnb_classics": bauer_station("rnb_classics", "R&B Classics", "rnb-classics"),
    "rnb_modern": bauer_station("rnb_modern", "R&B Modern", "rnb-modern"),
    "old_school_hiphop": bauer_station(
        "old_school_hiphop", "Old School Hiphop", "old-school-hiphop"
    ),
    "top_100_listen": bauer_station("top_100_listen", "Top 100 Listen", "top-100-listen"),
    "chillout_lounge": bauer_station("chillout_lounge", "Chillout Lounge", "chillout-lounge"),
    "meditation": bauer_station("meditation", "Meditation", "meditation"),
}

DEFAULT_STATION_IDS = ["dr_p1", "dr_p2", "dr_p3", "nova", "the_voice", "radio_100"]


def get_station(station_id: str) -> dict[str, Any]:
    """Return a copy of a built-in station by id."""
    try:
        return deepcopy(STATIONS[station_id])
    except KeyError as err:
        raise ValueError(f"Unknown Danish Radio station id: {station_id}") from err
