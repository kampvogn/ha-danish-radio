# Danish Radio

Home Assistant custom integration for Danish radio stations, streams, and now-playing metadata.

The integration lives in `custom_components/danish_radio`.

See [`custom_components/danish_radio/README.md`](custom_components/danish_radio/README.md) for installation and configuration.

## Radio app (Home Assistant package)

`packages/radio.yaml` is a ready-made radio "app" for Home Assistant, built
like a remote control: pick a player, then pick a station for it. Each player
remembers its own station, so several players can play at once, also
different stations. `sensor.radio_spiller_nu` lists every player playing radio
(for a "now playing" card with a stop-all button), and DR P3 on a TV plays the
studio webcam (HLS video with audio).

Players and stations are defined in one place, `sensor.radio_konfiguration`
in the package. Now-playing metadata comes from the `danish_radio`
integration; `scripts/dr_icy_now_playing.py p3webcam` finds the live P3 webcam
stream on dr.dk/lyd.

Dashboard example:

```yaml
- type: entities
  title: Radio
  entities:
    - entity: input_select.radio_afspiller
      name: Afspiller
    - entity: input_select.radio_station
      name: Station
    - entity: sensor.radio_valgt_station_info
      name: Nu spiller
    - entity: input_number.radio_volume
      name: Volumen
    # Only shown when the selected player has a remote (see below).
    - type: conditional
      conditions:
        - entity: binary_sensor.radio_valgt_afspiller_har_fjernbetjening
          state: "on"
      row:
        entity: sensor.radio_valgt_afspiller_tilbage_til
        name: Tilbage til
        tap_action: {action: perform-action, perform_action: script.radio_hjem_valgt}
  footer:
    type: buttons
    entities:
      - entity: binary_sensor.radio_valgt_afspiller_spiller
        tap_action: {action: perform-action, perform_action: script.radio_toggle_valgt}
      - entity: script.radio_stop_valgt
        icon: mdi:stop
        tap_action: {action: perform-action, perform_action: script.radio_stop_valgt}
      - entity: binary_sensor.radio_valgt_afspiller_mutet
        tap_action: {action: perform-action, perform_action: script.radio_mute_valgt}
- type: conditional
  conditions:
    - condition: numeric_state
      entity: sensor.radio_spiller_nu
      above: 0
  card:
    type: vertical-stack
    cards:
      - type: markdown
        title: Spiller nu
        content: >-
          {% for r in state_attr('sensor.radio_spiller_nu','afspillere') or [] %}**{{ r.navn }}** · {{ r.station }}{% if r.info %}
          {{ r.info }}{% endif %}

          {% endfor %}
      - type: button
        name: Stop alle
        icon: mdi:stop-circle-outline
        tap_action: {action: perform-action, perform_action: script.radio_stop_alle}
```

**Optional remote control.** If a player is a Chromecast with Google TV (or
another Android TV) paired with the
[Android TV Remote](https://www.home-assistant.io/integrations/androidtv_remote/)
integration, map it in the `fjernbetjeninger` attribute of
`sensor.radio_konfiguration` (`media_player` → `remote`). When radio starts on
that player, the app running on the TV (e.g. TV 2 Play) is remembered, and the
card shows a "Tilbage til TV 2 Play" row that closes the cast app and reopens
it (or goes to the home screen if radio was started from there). Friendly app
names come from `appnavne`. Without a mapping, or if the remote is unavailable, the button stays
hidden.

Also install the integration (`custom_components/danish_radio`); the package
configures its stations.

Install by copying the package and the script into your config:

```sh
cp packages/radio.yaml /config/packages/radio.yaml
cp scripts/dr_icy_now_playing.py /config/scripts/dr_icy_now_playing.py
```

The package expects `homeassistant: packages: !include_dir_named packages` in
`configuration.yaml`. Media player entity ids in the package are from the
author's home; adjust them to your own.
