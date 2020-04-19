# Media Player Lights Sync

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs) [![](https://img.shields.io/github/release/ericmatte/ad-media-lights-sync/all.svg?style=for-the-badge)](https://github.com/ericmatte/ad-media-lights-sync/releases)

<a href="https://www.buymeacoffee.com/ericmatte" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>

_AppDaemon App that synchronizes the color of RGB lights with the thumbnail of a media player in Home Assistant._

---

<img src="https://github.com/ericmatte/ad-media-lights-sync/raw/master/examples/example-1.jpg" alt="Example 1" width="400"> <img src="https://github.com/ericmatte/ad-media-lights-sync/raw/master/examples/example-2.jpg" alt="Example 1" width="400">

## Features

- Realtime RGB lights color synchronization with the thumbnail of a media player
- Extract most relevant colors from a picture and assign them to lights
- Always creates great matching moody ambiances
- Change all configured lights color at the same time using multithreading
- Prevent lights synchronization based on a state condition from your Home Assistant

## Installation

Use [HACS](https://hacs.xyz/) or download the `media_lights_sync` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `media_lights_sync` module.

## Prerequisites

In order for this app to work, you need to add the following packages to your main AppDaemon config:

```yaml
system_packages:
  - musl
  - make
  - g++
  - python3-dev
  - build-base
  - jpeg-dev
  - zlib-dev
python_packages:
  - Pillow
```

## App configuration

```yaml
media_lights_sync:
  module: media_lights_sync
  class: MediaLightsSync
  media_player: media_player.tv
  condition:
    entity: input_boolean.sync_tv_lights
    state: "on"
  lights:
    - light.left_theatre_light
    - light.right_theatre_light
```

| key                | optional | type   | default             | description                                                    |
| ------------------ | -------- | ------ | ------------------- | -------------------------------------------------------------- |
| `module`           | False    | string | `media_lights_sync` | The module name of the app.                                    |
| `class`            | False    | string | `MediaLightsSync`   | The name of the Class.                                         |
| `media_player`     | False    | string |                     | The entity_id of the media player to sync from.                |
| `condition`        | True     | object |                     | Sync lights only if the state of the condition entity is valid |
| `condition.entity` | False    | string |                     | The entity_id of the condition.                                |
| `condition.state`  | False    | string |                     | The state to match in order for the lights to sync.            |
| `lights`           | False    | list   |                     | The list of all the lights entity_id to sync to.               |

## Notes

- Based on `music_lights.py` from this project: https://github.com/astone123/appdaemon-apps.
- This code has only been tested using a ChromeCast and Phillips Hue lights.
- If you find a bug with another type of media player or light, PRs and detailed issues are welcome.
