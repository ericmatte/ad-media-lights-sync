"""Sample AppDaemon app for HACS."""
import appdaemon.plugins.hass.hassapi as hass


class Hacs(hass.Hass):
    """Hacs class."""

    def initialize(self):
        """Initialize the HACS app."""
        self.log("Sample AppDaemon app for HACS.")
        self.log("Pending updates in HACS: {}".format(self.get_pending_updates()))

    def get_pending_updates(self):
        """Get pending updates in HACS."""
        return self.get_state(self.hacs_sensor)

    @property
    def hacs_sensor(self):
        """Return the entity_id of the HACS sensor."""
        return self.args.get('hacs_sensor', 'sensor.hacs')
