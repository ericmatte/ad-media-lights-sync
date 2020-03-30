## App configuration

```yaml
hacs:
  module: hacs
  class: Hacs
  hacs_sensor: sensor.hacs
```

key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | | The module name of the app.
`class` | False | string | | The name of the Class.
`hacs_sensor` | True | string | `sensor.hacs`| The entity_id of the HACS sensor.
