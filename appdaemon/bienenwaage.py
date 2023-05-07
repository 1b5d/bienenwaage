from appdaemon.plugins.hass.hassapi import Hass
from hx711 import HX711

MODE_NORMAL = 1
MODE_CALIBRATE = 2
MODE_RESET = 4


class Bienenwaage(Hass):
    interval = 10
    mode = MODE_NORMAL

    def initialize(self):
        self.sensor = self.get_entity(self.args['sensor'])
        self.refunit_sensor = self.get_entity(self.args['refunit_sensor'])

        refunit = float(self.refunit_sensor.get_state() or 1)
        last_session_reading = float(self.sensor.get_state() or 0)
        self.log(
            f"initialisierung mit letzter Lesung: {last_session_reading}, refunit: {refunit}"
        )

        self.hx = HX711(self.args['dout'], self.args['pd_sck'],
                        self.args['gain'])
        self.hx.set_reading_format("MSB", "MSB")
        self.hx.set_reference_unit(refunit)
        self._tare(extra=last_session_reading)

        self.run_every(self.measure, "now+10", self.interval)
        self.listen_event(self.calibrate, self.args['calibration_event'])
        self.listen_event(self.tare, self.args['tare_event'])

    def calibrate(self, event, data, kwargs):
        if self.mode != MODE_NORMAL:
            self.log("kann nur im Normalmodus kalibrieren")
            return

        self.mode = MODE_CALIBRATE
        cal_sample = float(data.get('sample', 1))
        self.log("Kalibriermodus an")
        self.hx.set_reference_unit(1)
        self.hx.reset()
        val = self.hx.get_weight(5)
        refunit = val / cal_sample
        self.hx.set_reference_unit(refunit)
        self.hx.reset()
        self.refunit_sensor.set_state(state=refunit)
        self.mode = MODE_NORMAL
        self.log(f"refunit: {refunit}")
        self.log("Kalibriermodus aus")

    def _tare(self, extra=0, times=15):
        self.hx.reset()
        backupReferenceUnit = self.hx.get_reference_unit_A()
        self.hx.set_reference_unit_A(1)
        value = self.hx.read_average(15)
        value -= extra * backupReferenceUnit
        self.hx.set_offset_A(value)
        self.hx.set_reference_unit_A(backupReferenceUnit)

    def tare(self, event, data, kwargs):
        if self.mode != MODE_NORMAL:
            self.log("kann nur im Normalmodus reset machen")
            return

        self.mode = MODE_RESET
        self._tare(extra=float(data.get('tare', 0)))

        self.mode = MODE_NORMAL

    def measure(self, kwargs):
        if self.mode != MODE_NORMAL:
            self.log("nicht im Normalmodus")
            return

        val = self.hx.get_weight(5)
        self.sensor.set_state(state=val)

        self.hx.power_down()
        self.hx.power_up()