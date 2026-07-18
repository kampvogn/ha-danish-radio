# Danish Radio

Home Assistant custom integration for Danish radio stations, streams, and now-playing metadata.

This first MVP supports YAML configuration and creates one sensor per station.

## Providers

- `icy`: generic ICY/Shoutcast metadata.
- `dr`: DR current programme API plus ICY song metadata.
- `bauer_rayo`: Bauer/Rayo station page JSON plus ICY fallback.

## Example

```yaml
danish_radio:
  stations:
    - name: DR P3
      station_id: dr_p3
      provider: dr
      schedule_slug: p3
      stream_url: https://live-icy.dr.dk/A/A05H.mp3
      scan_interval:
        hours: 1

    - name: NOVA
      station_id: nova
      provider: bauer_rayo
      rayo_slug: nova
      stream_url: https://live-bauerdk.sharp-stream.com/nova_dk_mp3?direct=true
      scan_interval:
        hours: 1
```

Each sensor exposes normalized attributes:

- `station`
- `program`
- `artist`
- `title`
- `stream_title`
- `image`
- `source`
- `updated_at`

## Notes

This is not yet a full HACS/config-flow integration. Next steps:

- Config flow and options flow.
- Services for manual update / station playback helpers.
- Optional AcoustID/Chromaprint fallback.
- Tests and typed provider modules.
