# Danish Radio

Home Assistant custom integration for Danish radio stations, streams, and now-playing metadata.

The integration lives in `custom_components/danish_radio`.

See [`custom_components/danish_radio/README.md`](custom_components/danish_radio/README.md) for installation and configuration.

## Radio app (Home Assistant package)

`packages/radio.yaml` is a ready-made radio "app" for Home Assistant: station and
player selectors, play/pause/stop/mute scripts, volume sync and now-playing
sensors. It uses `scripts/dr_icy_now_playing.py` for metadata.

Install by copying both files into your config:

```sh
cp packages/radio.yaml /config/packages/radio.yaml
cp scripts/dr_icy_now_playing.py /config/scripts/dr_icy_now_playing.py
```

The package expects `homeassistant: packages: !include_dir_named packages` in
`configuration.yaml`. Media player entity ids in the package are from the
author's home; adjust them to your own.
