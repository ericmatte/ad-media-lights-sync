"""Synchronize RGB lights with media player thumbnail"""
import appdaemon.plugins.hass.hassapi as hass
import sys
import io
import colorsys

from threading import Thread
from PIL import Image
from urllib.parse import urljoin
from urllib.request import urlopen

PICTURE_ATTRIBUTES = ["entity_picture_local", "entity_picture"]


class MediaLightsSync(hass.Hass):
    """MediaLightsSync class."""

    def initialize(self):
        """Initialize the app and listen for media_player photo_attribute changes."""
        args = self.args
        self.lights = args["lights"]
        self.ha_url = args.get("ha_url", None)
        self.condition = args.get("condition")
        self.transition = args.get("transition", None)
        self.reset_lights_after = args.get("reset_lights_after", False)
        self.use_saturated_colors = args.get("use_saturated_colors", False)
        self.brightness = None if args.get("use_current_brightness", False) else 255

        self.media_player_callbacks = {}
        self.initial_lights_states = None
        media_players = args["media_player"] if isinstance(args["media_player"], list) else [args["media_player"]]

        for media_player in media_players:
            for photo_attribute in PICTURE_ATTRIBUTES:
                self.listen_state(self.change_lights_color, media_player, attribute=photo_attribute)

    def change_lights_color(self, entity, attribute, old_url, new_url, kwargs):
        """Callback when a entity_picture has changed."""
        if new_url == old_url or not self.can_change_colors():
            return

        if new_url is not None:
            self.store_initial_lights_states()
            log_message = "New picture received from '{entity}' ({attr})\n"
            current_pictures = [self.get_state(entity, attr) for attr in PICTURE_ATTRIBUTES]
            if self.media_player_callbacks.get(entity, None) == current_pictures:
                # Image already processed from another callback
                return

            rgb_colors = self.get_colors(self.format_url(new_url))
            self.media_player_callbacks[entity] = current_pictures
            for i in range(len(self.lights)):
                color = self.get_saturated_color(rgb_colors[i]) if self.use_saturated_colors else rgb_colors[i]
                self.set_light("on", self.lights[i], color=color, brightness=self.brightness, transition=self.transition)
        else:
            self.reset_lights()

    def can_change_colors(self):
        """Validate that light should be sync if a condition is set."""
        return self.condition is None or self.get_state(self.condition["entity"]) == self.condition["state"]

    def store_initial_lights_states(self):
        """Save the initial state of all lights if not already done."""
        if self.reset_lights_after and self.initial_lights_states is None:
            self.initial_lights_states = [self.get_state(self.lights[i], attribute="all") for i in range(len(self.lights))]

    def reset_lights(self):
        """Reset lights to their initial state after turning off a medial_player."""
        if self.reset_lights_after and self.initial_lights_states is not None:
            for i in range(len(self.lights)):
                state = self.initial_lights_states[i]["state"]
                attributes = self.initial_lights_states[i]["attributes"]
                self.set_light(state.lower(), self.lights[i], color=attributes.get("rgb_color", None), brightness=attributes.get("brightness", None), transition=self.transition)
            self.initial_lights_states = None

    def set_light(self, new_state, entity, color=None, brightness=None, transition=None):
        """Change the color of a light."""
        attributes = {}
        if transition is not None:
            attributes["transition"] = transition

        if new_state == "off":
            Thread(target=self.turn_off, args=[entity], kwargs=attributes).start()
        else:
            attributes["rgb_color"] = color
            if brightness is not None:
                attributes["brightness"] = brightness
            Thread(target=self.turn_on, args=[entity], kwargs=attributes).start()

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

    def format_url(self, url):
        """Append ha_url if this is a relative url"""
        is_relative = not url.startswith("http")
        if not is_relative:
            return url
        elif is_relative and self.ha_url is None:
            raise ValueError("ha_url must be specified when using relative url for photo_attribute.")
        else:
            return urljoin(self.ha_url, url)
