"""Synchronize RGB lights with media player thumbnail"""
import appdaemon.plugins.hass.hassapi as hass
import sys
import threading
import io
import colorsys

from PIL import Image
from urllib.parse import urljoin
from urllib.request import urlopen


class MediaLightsSync(hass.Hass):
    """MediaLightsSync class."""

    def initialize(self):
        """Initialize the app and listen for media_player photo_attribute changes."""
        self.ha_url = self.args.get("ha_url", None)
        self.use_current_brightness = self.args.get("use_current_brightness", False)
        self.condition = self.args.get("condition")
        self.transition = self.args.get("transition", None)
        self.lights = self.args["lights"]
        self.use_saturated_colors = self.args.get("use_saturated_colors", False)

        photo_attribute = self.args.get("photo_attribute", "entity_picture")
        self.listen_state(self.change_lights_color, self.args["media_player"], attribute=photo_attribute)

    def change_lights_color(self, entity, attribute, oldUrl, newUrl, kwargs):
        """Callback when the photo_attribute has changed."""
        if newUrl != oldUrl and newUrl is not None and self.can_change_colors():
            rgb_colors = self.get_colors(self.format_ha_url(newUrl))
            for i in range(len(self.lights)):
                threading.Thread(target=self.set_light_rgb, args=(self.lights[i], rgb_colors[i])).start()

    def can_change_colors(self):
        """Validate that light should be sync if a condition is set."""
        return self.condition is None or self.get_state(self.condition["entity"]) == self.condition["state"]

    def set_light_rgb(self, light, color):
        """Change a light color."""
        light_kwargs = {"rgb_color": color}
        if self.use_saturated_colors:
            light_kwargs["rgb_color"] = self.get_saturated_color(color)
        if not self.use_current_brightness:
            light_kwargs["brightness"] = 255
        if self.transition is not None:
            light_kwargs["transition"] = self.transition
        self.turn_on(light, **light_kwargs)

    def get_saturated_color(self, color):
        """Increase the saturation of the current color."""
        hls = colorsys.rgb_to_hls(color[0] / 255, color[1] / 255, color[2] / 255)
        rgb_saturated = colorsys.hls_to_rgb(hls[0], 0.5, 0.5)
        return [int(rgb_saturated[0] * 255), int(rgb_saturated[1] * 255), int(rgb_saturated[2] * 255)]

    def get_colors(self, url):
        """Get the palette of colors from url."""
        fd = urlopen(url)
        f = io.BytesIO(fd.read())
        im = Image.open(f)
        palette = im.quantize(colors=len(self.lights)).getpalette()
        return self.extract_colors(palette, len(self.lights))

    def extract_colors(self, palette, colors):
        """Extract an amount of colors corresponding to the amount of lights in the configuration."""
        return [palette[i:i + 3] for i in range(0, colors * 3, 3)]

    def format_ha_url(self, url):
        """Append ha_url if this is a relative url"""
        is_relative = not url.startswith("http")
        if not is_relative:
            return url
        elif is_relative and self.ha_url is None:
            raise ValueError("ha_url must be specified when using relative url for photo_attribute.")
        else:
            return urljoin(self.ha_url, url)
