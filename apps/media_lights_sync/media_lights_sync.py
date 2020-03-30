"""Synchronize RGB lights with media player thumbnail"""
import appdaemon.plugins.hass.hassapi as hass
import sys
import threading
import io
from PIL import Image

if sys.version_info < (3, 0):
    from urllib2 import urlopen
else:
    from urllib.request import urlopen

class MediaLightsSync(hass.Hass):
  """MediaLightsSync class."""
 
  def initialize(self):
    """Initialize the app and listen for media_player photo_attribute changes."""
    self.condition = self.args.get("condition")
    self.lights = self.args["lights"]
    self.listen_state(self.change_lights_color, self.args["media_player"], attribute = self.args.get("photo_attribute", "entity_picture"))

  def change_lights_color(self, entity, attribute, oldUrl, newUrl, kwargs):
    """Callback when the photo_attribute has changed."""
    if newUrl != oldUrl and newUrl is not None and self.can_change_colors():
      rgb_colors = self.get_colors(newUrl)
      for i in range(len(self.lights)):
        threading.Thread(target=self.set_light_rgb, args=(self.lights[i], rgb_colors[i])).start()

  def can_change_colors(self):
    """Validate that light should be sync if a condition is set."""
    return self.condition is None or self.get_state(self.condition["entity"]) == self.condition["state"]

  def set_light_rgb(self, light, color):
    """Change a light color."""
    self.turn_on(light, rgb_color=color, brightness=255)

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