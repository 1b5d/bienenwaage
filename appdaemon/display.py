from appdaemon.plugins.hass.hassapi import Hass

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont


class Display(Hass):
    interval = 10

    def initialize(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial)
        self.sensor1 = self.get_entity(self.args['sensor1'])
        self.sensor2 = self.get_entity(self.args['sensor2'])
        self.sensor3 = self.get_entity(self.args['sensor3'])
        self.sensor4 = self.get_entity(self.args['sensor4'])
        self.sensor5 = self.get_entity(self.args['sensor5'])
        self.sensor6 = self.get_entity(self.args['sensor6'])
        self.lines = {}
        self.run_every(self.refresh, "now+10", self.interval)

    def refresh(self, kwargs):
        self.lines[0] = int(float(self.sensor1.get_state() or 0))
        self.lines[1] = int(float(self.sensor2.get_state() or 0))
        self.lines[2] = int(float(self.sensor3.get_state() or 0))
        self.lines[3] = int(float(self.sensor4.get_state() or 0))
        self.lines[4] = int(float(self.sensor5.get_state() or 0))
        self.lines[5] = int(float(self.sensor6.get_state() or 0))

        oled_font = ImageFont.load_default()
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box,
                           outline="white",
                           fill="black")

            for (line_id, line) in self.lines.items():
                draw.text((10, 2 + line_id * 10),
                          f'w{line_id + 1}: {str(int(line))} g',
                          font=oled_font,
                          fill="white")