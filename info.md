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
