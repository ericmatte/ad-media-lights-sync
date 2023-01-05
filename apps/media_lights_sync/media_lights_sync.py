"""Synchronize RGB lights with media player thumbnail"""
import appdaemon.plugins.hass.hassapi as hass
import sys
import io
import colorsys
import ssl

from threading import Thread
from PIL import Image, features
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

PICTURE_ATTRIBUTES = ["entity_picture_local", "entity_picture"]

COLOR_MODES = {
    "rgb": "rgb_color",
    "xy": "xy_color",
    "color_temp": "color_temp",
}


class MediaLightsSync(hass.Hass):
    """MediaLightsSync class."""

    def initialize(self):
        """Initialize the app and listen for media_player photo_attribute changes."""
        args = self.args
        self.lights = args["lights"]
        self.ha_url = args.get("ha_url", None)
        self.verify_cert = args.get("verify_cert", True)
        self.condition = args.get("condition")
        self.transition = args.get("transition", None)
        self.reset_lights_after = args.get("reset_lights_after", False)
        self.use_saturated_colors = args.get("use_saturated_colors", False)
        self.brightness = None if args.get("use_current_brightness", False) else 255
        self.quantization_method = self.get_quantization_method(args.get("quantization_method", None))

        self.media_player_callbacks = {}
        self.initial_lights_states = None
        media_players = args["media_player"] if isinstance(args["media_player"], list) else [args["media_player"]]

        for media_player in media_players:
            self.log("Listening for picture changes on '{entity}'".format(entity=media_player))
            for photo_attribute in PICTURE_ATTRIBUTES:
                self.listen_state(self.change_lights_color, media_player, attribute=photo_attribute)

    def change_lights_color(self, entity, attribute, old_url, new_url, kwargs):
        """Callback when a entity_picture has changed."""
        if new_url == old_url or not self.can_change_colors():
            return

        if new_url is not None:
            self.store_initial_lights_states()
            log_message = "New picture received from '{entity}' ({attribute})\n"
            current_pictures = [self.get_state(entity, attribute=attribute) for attribute in PICTURE_ATTRIBUTES]

            if self.media_player_callbacks.get(entity, None) == current_pictures:
                # Image already processed from another callback
                return self.log(log_message.format(entity=entity, attribute=attribute + "; skipped"))
            self.log(log_message.format(entity=entity, attribute=attribute))

            try:
                url = self.format_url(new_url, entity, attribute)
                rgb_colors = self.get_colors(url)
            except (HTTPError, URLError) as error:
                self.error("Unable to fetch artwork: {error}\nURL: {url}\n".format(url=url, error=error))
                return

            self.media_player_callbacks[entity] = current_pictures
            for i in range(len(self.lights)):
                color = self.get_saturated_color(rgb_colors[i]) if self.use_saturated_colors else rgb_colors[i]
                if color == [0, 0, 0]:
                    self.log("Skipped black color for '{entity}' light".format(entity=self.lights[i]))
                    continue
                self.set_light("on", self.lights[i], color=color, brightness=self.brightness, transition=self.transition)
        else:
            self.reset_lights()

    def can_change_colors(self):
        """Validate that light should be sync if a condition is set."""
        if self.condition is None:
            return True
        elif "value_template" in self.condition:
            return self.render_template(self.condition["value_template"]) == True
        else:
            return self.get_state(self.condition["entity"]) == self.condition["state"]

    def store_initial_lights_states(self):
        """Save the initial state of all lights if not already done."""
        if self.reset_lights_after and self.initial_lights_states is None:
            self.initial_lights_states = [self.get_state(self.lights[i], attribute="all") for i in range(len(self.lights))]

    def reset_lights(self):
        """Reset lights to their initial state after turning off a medial_player."""
        if self.reset_lights_after and self.initial_lights_states is not None:
            self.log("Resetting lights\n")
            for i in range(len(self.lights)):
                state = self.initial_lights_states[i]["state"]
                attributes = self.initial_lights_states[i]["attributes"]
                color_attr = COLOR_MODES.get(attributes.get("color_mode", None), "rgb_color")

                self.set_light(state.lower(), self.lights[i], color=attributes.get(color_attr, None), color_attr=color_attr,
                               brightness=attributes.get("brightness", None), transition=self.transition)
            self.initial_lights_states = None
            self.media_player_callbacks = {}

    def set_light(self, new_state, entity, color=None, color_attr="rgb_color", brightness=None, transition=None):
        """Change the color of a light."""
        attributes = {}
        if transition is not None:
            attributes["transition"] = transition

        if new_state == "off":
            self.log("Turn off '{entity}' light".format(entity=entity))
            Thread(target=self.turn_off, args=[entity], kwargs=attributes).start()
        else:
            attributes[color_attr] = color
            if brightness is not None:
                attributes["brightness"] = brightness
            self.log("Set '{entity}' light:\n{attributes}".format(entity=entity, attributes=attributes))
            Thread(target=self.turn_on, args=[entity], kwargs=attributes).start()

    def get_saturated_color(self, color):
        """Increase the saturation of the current color."""
        hls = colorsys.rgb_to_hls(color[0] / 255, color[1] / 255, color[2] / 255)
        rgb_saturated = colorsys.hls_to_rgb(hls[0], 0.5, 0.5)
        return [int(rgb_saturated[0] * 255), int(rgb_saturated[1] * 255), int(rgb_saturated[2] * 255)]

    def get_colors(self, url):
        """Get the palette of colors from url."""
        context = ssl.SSLContext() if not self.verify_cert else None
        fd = urlopen(url, context=context)
        f = io.BytesIO(fd.read())
        im = Image.open(f)
        if im.mode == "RGBA" and self.quantization_method not in [None, Image.FASTOCTREE, Image.LIBIMAGEQUANT]:
            im = self.convert_rgba_to_rgb(im)

        palette = im.quantize(colors=len(self.lights), method=self.quantization_method).getpalette()
        return self.extract_colors(palette, len(self.lights))

    def convert_rgba_to_rgb(self, rgba_image):
        rgba_image.load()  # required for png.split()
        rgb_image = Image.new("RGB", rgba_image.size, (255, 255, 255))
        rgb_image.paste(rgba_image, mask=rgba_image.split()[3])  # 3 is the alpha channel
        return rgb_image

    def get_quantization_method(self, value):
        method = None
        if value == "FastOctree":
            method = Image.FASTOCTREE
        elif value == "MedianCut":
            method = Image.MEDIANCUT
        elif value == "MaxCoverage":
            method = Image.MAXCOVERAGE
        elif value == "libimagequant":
            if features.check_feature(feature="libimagequant"):
                method = Image.LIBIMAGEQUANT
            else:
                self.log("Quantization method 'libimagequant' is unsupported by your platform.")
        self.log("Using {method} quantization method".format(method="default" if method is None else value))
        return method

    def extract_colors(self, palette, colors):
        """Extract an amount of colors corresponding to the amount of lights in the configuration."""
        return [palette[i:i + 3] for i in range(0, colors * 3, 3)]

    def format_url(self, url, entity, attribute):
        """Append ha_url if this is a relative url"""
        is_absolute = bool(urlparse(url).netloc) or url.startswith("file:///")
        if is_absolute:
            return url
        elif not is_absolute and self.ha_url is None:
            raise ValueError("A relative URL was received on '{entity}.{attribute}'.\nha_url must be specified in the configuration for relative URLs.".format(
                entity=entity, attribute=attribute))
        else:
            return urljoin(self.ha_url, url)
