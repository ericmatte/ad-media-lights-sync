## App configuration

```yaml
media_lights_sync:
  module: media_lights_sync
  class: MediaLightsSync
  media_player: media_player.tv
  photo_attribute: entity_picture
  ha_url: !secret ha_url
  use_current_brightness: false
  condition:
    entity: input_boolean.sync_tv_lights
    state: "on"
  lights:
    - light.left_theatre_light
    - light.right_theatre_light
```

| key                      | optional | type           | default             | description                                                                                                                                                                                     |
| ------------------------ | -------- | -------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `module`                 | False    | string         | `media_lights_sync` | The module name of the app.                                                                                                                                                                     |
| `class`                  | False    | string         | `MediaLightsSync`   | The name of the Class.                                                                                                                                                                          |
| `media_player`           | False    | string or list |                     | The entity_id(s) of the media player(s) to sync from<sup id="ha-url">[1](#ha-url-note)</sup>.                                                                                                   |
| `photo_attribute`        | True     | string         | `entity_picture`    | The state attribute containing the url to the thumbnail. Examples: `entity_picture`, `entity_picture_local`.                                                                                    |
| `ha_url`                 | True     | string         | `null`              | The URL to your Home Assistant. Only useful if `photo_attribute` is a relative URL<sup id="ha-url">[1](#ha-url-note)</sup>. Examples: `https://my-ha.duckdns.org`, `http://192.168.1.123:8123`. |
| `use_saturated_colors`   | True     | bool           | `false`             | Increase the saturation and brightness of the colors.                                                                                                                                           |
| `use_current_brightness` | True     | bool           | `false`             | Do not change lights brightness. If `false`, it will always sets all lights to maximum brightness.                                                                                              |
| `transition`             | True     | number         | `null`              | Number that represents the time (in seconds) the light should take to transition to new states.                                                                                                 |
| `condition`              | True     | object         |                     | Sync lights only if the state of the condition entity is valid.                                                                                                                                 |
| `condition.entity`       | False    | string         |                     | The entity_id of the condition.                                                                                                                                                                 |
| `condition.state`        | False    | string         |                     | The state to match in order for the lights to sync.                                                                                                                                             |
| `lights`                 | False    | list           |                     | The list of all the lights entity_id to sync to.                                                                                                                                                |

<b id="ha-url-note">[1](#ha-url)</b>: See `/developer-tools/state` in your Home Assistant instance.
