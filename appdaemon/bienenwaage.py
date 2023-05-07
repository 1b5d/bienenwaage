from appdaemon.plugins.hass.hassapi import Hass
from hx711 import HX711

MODE_NORMAL = 1
MODE_CALIBRATE = 2


class Bienenwaage(Hass):
    interval = 10
    mode = MODE_NORMAL

    def initialize(self):
        self.sensor = self.get_entity(self.args['sensor'])
        self.refunit_sensor = self.get_entity(self.args['refunit_sensor'])
        self.offset_sensor = self.get_entity(self.args['offset_sensor'])

        refunit = float(self.refunit_sensor.get_state() or 1)
        offset = float(self.offset_sensor.get_state() or 0)
        self.log(f"Initilizing with refunit: {refunit}, offset: {offset}")

        self.hx = HX711(self.args['dout'], self.args['pd_sck'],
                        self.args['gain'])
        self.hx.set_reading_format("MSB", "MSB")

        self.hx.set_offset(offset)
        self.hx.set_reference_unit(refunit)
        self.hx.reset()

        self.run_every(self.measure, "now+10", self.interval)
        self.listen_event(self.calibrate, self.args['calibration_event'])
        self.listen_event(self.tare, self.args['tare_event'])

    def calibrate(self, event, data, kwargs):
        if self.mode != MODE_NORMAL:
            self.log("Can only calibrate in normal mode, ignoring")
            return

        self.mode = MODE_CALIBRATE
        cal_sample = float(data.get('sample', 1))
        self.log(f"Calibration started with sample {cal_sample}")

        self.hx.set_reference_unit(1)

        val = self.hx.get_value(15)
        self.log(f"Sensor reading: {val}")

        refunit = val / cal_sample

        self.hx.set_reference_unit(refunit)
        self.hx.reset()

        self.refunit_sensor.set_state(state=refunit)
        self.mode = MODE_NORMAL
        self.log(f"Calibration finished, refunit: {refunit}")

    def tare(self, event, data, kwargs):
        tare_value = float(data.get('tare', 0))
        refunit = float(self.refunit_sensor.get_state() or 1)
        self.hx.set_reference_unit(1)
        value = self.hx.read_average(15)
        self.log(f"Sensor reading: {value}")
        value -= tare_value * refunit
        self.hx.set_offset(value)
        self.offset_sensor.set_state(state=value)
        self.hx.set_reference_unit(refunit)
        self.hx.reset()
        self.log(f"tare set to {tare_value}")

    def measure(self, kwargs):
        if self.mode != MODE_NORMAL:
            self.log("Error: can only take measurement in in normal mode")
            return

        val = self.hx.get_weight(5)
        self.sensor.set_state(state=val)

        self.hx.power_down()
        self.hx.power_up()