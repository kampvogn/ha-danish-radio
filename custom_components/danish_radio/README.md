# Danish Radio

Home Assistant custom integration for Danish radio stations, streams, and now-playing metadata.

This project is an early MVP. It currently supports YAML configuration and creates one sensor per selected station. Each sensor exposes normalized metadata attributes for programme, artist, title, artwork, stream URL, and provider source.

## Installation

### HACS custom repository

1. Add this repository as a HACS custom repository.
2. Select category `Integration`.
3. Install `Danish Radio`.
4. Restart Home Assistant.
5. Add YAML configuration and restart Home Assistant again.

### Manual install

Copy `custom_components/danish_radio` into your Home Assistant `custom_components` directory and restart Home Assistant.

## Configuration

Use built-in station ids:

```yaml
danish_radio:
  stations:
    - dr_p1
    - dr_p2
    - dr_p3
    - dr_p4_koebenhavn
    - dr_p6_beat
    - dr_p8_jazz
    - nova
    - the_voice
    - radio_100
    - pop_fm
    - radio_soft
    - myrock
```

If `danish_radio:` is configured without a `stations` list, the integration defaults to:

```yaml
danish_radio:
```

which loads `dr_p1`, `dr_p2`, `dr_p3`, `nova`, `the_voice`, and `radio_100`.

You can also define a custom station:

```yaml
danish_radio:
  stations:
    - name: Example Station
      station_id: example_station
      provider: icy
      stream_url: https://example.com/live.mp3
      scan_interval:
        minutes: 10
```

## Built-in Stations

### DR

- `dr_p1`
- `dr_p2`
- `dr_p3`
- `dr_p4_bornholm`
- `dr_p4_esbjerg`
- `dr_p4_fyn`
- `dr_p4_koebenhavn`
- `dr_p4_midt_vest`
- `dr_p4_nordjylland`
- `dr_p4_sjaelland`
- `dr_p4_syd`
- `dr_p4_trekanten`
- `dr_p4_oestjylland`
- `dr_p5_koebenhavn`
- `dr_p6_beat`
- `dr_p8_jazz`

### Bauer/Rayo

- `nova`
- `the_voice`
- `radio_100`
- `pop_fm`
- `radio_soft`
- `myrock`
- `radio_klassisk`
- `radiovinyl`
- `mix`
- `nova_top_40`
- `nova_100_dansk`
- `go_nova_i_doegndrift`
- `nova_sommerhits`
- `myrock_legends`
- `planet_rock`
- `radio_soft_classic`
- `radio_soft_modern`
- `pop_fm_80er`
- `pop_fm_90er`
- `the_voice_in_the_mix`
- `the_voice_throwback`
- `the_voice_urban`
- `the_voice_k_pop`
- `00s_hits`
- `10s_hits`
- `70er_hits`
- `80s_hits`
- `90s_hits`
- `danske_80er_hits`
- `danske_90er_hits`
- `danske_00er_hits`
- `ny_dansk_musik`
- `dansktop_favoritter`
- `country_classics`
- `country_modern`
- `rnb_classics`
- `rnb_modern`
- `old_school_hiphop`
- `top_100_listen`
- `chillout_lounge`
- `meditation`

## Providers

- `icy`: generic ICY/Shoutcast metadata.
- `dr`: DR current programme API plus ICY song metadata.
- `bauer_rayo`: Bauer/Rayo station page JSON plus ICY fallback.

## Sensor Attributes

Each sensor exposes:

- `station`
- `program`
- `program_start`
- `program_end`
- `program_slug`
- `program_description`
- `artist`
- `title`
- `stream_title`
- `raw_metadata`
- `stream_url`
- `image`
- `source`
- `updated_at`

## Next Steps

- Config flow and options flow.
- Playback helper services.
- More station providers for non-DR/non-Bauer Danish stations.
- Tests for provider parsing and station registry validation.
- Optional AcoustID/Chromaprint fallback for streams without useful metadata.
