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

In order for this app to work, you need to add `py3-pillow` and `Pillow` to the config of your AppDaemon 4 Supervisor add-on:

```yaml
system_packages:
  - py3-pillow
python_packages:
  - Pillow
init_commands: []
log_level: info
```

If you are running AppDaemon in your own docker container, you must create and build a docker image with the above dependencies using a [Dockerfile](https://docs.docker.com/engine/reference/builder/) similar to this (**untested**):

```Dockerfile
FROM acockburn/appdaemon:latest
# Manually install the dependencies
RUN apk add py3-pillow
RUN pip3 install Pillow
```

## App configuration

`config/appdaemon/apps/apps.yaml`

```yaml
media_lights_sync:
  module: media_lights_sync
  class: MediaLightsSync
  media_player: media_player.tv
  lights:
    - light.left_theatre_light
    - light.right_theatre_light
  ha_url: !secret ha_url
  reset_lights_after: true
  use_saturated_colors: false
  use_current_brightness: false
  condition:
    entity: input_boolean.sync_tv_lights
    state: "on"
```

| key                      | optional | type           | default             | description                                                                                                                 |
| ------------------------ | -------- | -------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `module`                 | False    | string         | `media_lights_sync` | The module name of the app.                                                                                                 |
| `class`                  | False    | string         | `MediaLightsSync`   | The name of the Class.                                                                                                      |
| `media_player`           | False    | string or list |                     | The entity_id(s) of the media player(s) to sync from<sup id="ha-url">[1](#ha-url-note)</sup>.                               |
| `lights`                 | False    | list           |                     | The list of all the lights entity_id to sync to.                                                                            |
| `ha_url`                 | True     | string         | `null`              | The URL to your Home Assistant. Examples: `https://my-ha.duckdns.org`, `http://192.168.1.123:8123`.                         |
| `reset_lights_after`     | True     | bool           | `false`             | Reset lights to their initial state after turning off a `medial_player`. Will not reset lights if `false`.                  |
| `quantization_method`    | True     | string         | `MedianCut`         | Supports `MedianCut`, `FastOctree`, `MaxCoverage` and `libimagequant`. More info [below](#selecting-a-quantization_method). |
| `use_saturated_colors`   | True     | bool           | `false`             | Increase the saturation and brightness of the colors.                                                                       |
| `use_current_brightness` | True     | bool           | `false`             | Do not change lights brightness. If `false`, it will always sets all lights to maximum brightness.                          |
| `transition`             | True     | number         | `null`              | Number that represents the time (in seconds) the light should take to transition to new states.                             |
| `condition`              | True     | object         |                     | Sync lights only if the state of the condition entity is valid.                                                             |
| `condition.entity`       | False    | string         |                     | The entity_id of the condition.                                                                                             |
| `condition.state`        | False    | string         |                     | The state to match in order for the lights to sync.                                                                         |

<b id="ha-url-note">[1](#ha-url)</b>: See `/developer-tools/state` in your Home Assistant instance. This app will listen to changes on `entity_picture_local` and/or `entity_picture` attributes of your `media_player` entities.

## Selecting a `quantization_method`

There is four [quantization method](https://pillow.readthedocs.io/en/stable/reference/Image.html?highlight=getpalette#quantization-methods) available, which change the way the colors palette is extracted:

- `MedianCut`: Default method. Mix colors in the image using their median value.
- `FastOctree`: Extract dominant colors. Use this option if you want more accurate colors.
- `MaxCoverage`: Mix colors based on their maximum coverage.
- `libimagequant`: High-quality conversion of RGBA images to 8-bit indexed-color (palette) images.

Alternatively, you can also combine this option with `use_saturated_colors` to get more vibrant colors.

## Compatibility

This app should work with any `media_player` and RGB light integrations available in Home Assitant.
That said, it has been tested and is working with the following devices:

- **Media Players**:
  - ChromeCast
  - Apple TV ([hass-atv-beta](https://github.com/postlund/hass-atv-beta))
  - Kodi
  - All Amazon media players (Fire TV, Echo Dot, Echo Show, etc.)
  - [Spotify Integration](https://www.home-assistant.io/integrations/spotify/)
- **RGB Lights**:
  - Philips Hue
  - [ESPHome RGB Light](https://esphome.io/components/light/rgb.html) using an ESP8266
  - Z-Wave
  - Lifx
  - TP-Link
  - Yeelight (YLDP02YL, YLDD02YL)

_If you've found that this app is working with another device, just let me know so I can update this list._

## Notes

- Based on `music_lights.py` from this project: https://github.com/astone123/appdaemon-apps.
- If you find a bug with another type of media player or light, PRs and detailed issues are welcome.
