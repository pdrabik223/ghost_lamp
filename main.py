from math import floor
import random
import time

import requests
from pi_pico_neopixel_tools.color import Color
from pi_pico_neopixel_tools.led_strip import LedStrip
from pi_pico_w_server_tools.app import *
import ntptime
from machine import Pin, RTC
import _thread

sun_colors = [
    Color(255, 183, 77),  # dawn
    Color(255, 204, 128),  # early morning
    Color(255, 224, 178),  # morning
    Color(255, 241, 210),  # late morning
    Color(255, 250, 235),  # noon
    Color(255, 239, 210),  # afternoon
    Color(255, 205, 120),  # golden hour
    Color(255, 145, 65),  # sunset
    Color(220, 85, 55),  # late sunset
    Color(120, 65, 110),  # dusk
    Color(45, 40, 85),  # twilight
]

vibrant_colors = [
    # Vibrant pinks
    Color(255, 145, 180),
    Color(255, 138, 176),
    Color(255, 131, 172),
    Color(255, 124, 168),
    Color(255, 117, 164),
    Color(255, 110, 160),
    Color(255, 103, 156),
    Color(255, 96, 152),
    Color(255, 89, 148),
    Color(255, 82, 144),
    # Pink → peach
    Color(255, 82, 137),
    Color(255, 88, 130),
    Color(255, 94, 123),
    Color(255, 100, 116),
    Color(255, 106, 109),
    Color(255, 112, 102),
    Color(255, 118, 95),
    Color(255, 124, 88),
    Color(255, 130, 81),
    Color(255, 136, 74),
    # Vibrant peach / orange
    Color(255, 145, 70),
    Color(255, 153, 72),
    Color(255, 161, 74),
    Color(255, 169, 76),
    Color(255, 177, 78),
    Color(255, 185, 80),
    Color(255, 193, 82),
    Color(255, 201, 84),
    Color(255, 209, 86),
    Color(255, 217, 88),
    # Peach → yellow
    Color(255, 220, 75),
    Color(255, 224, 65),
    Color(255, 228, 55),
    Color(255, 232, 45),
    Color(255, 236, 35),
    Color(255, 240, 25),
    Color(255, 244, 20),
    Color(255, 248, 18),
    Color(255, 252, 16),
    Color(255, 255, 14),
    # Vibrant yellows
    Color(248, 255, 20),
    Color(240, 255, 25),
    Color(232, 255, 30),
    Color(224, 255, 35),
    Color(216, 255, 40),
    Color(208, 255, 45),
    Color(200, 255, 50),
    Color(192, 255, 55),
    Color(184, 255, 60),
    Color(176, 255, 65),
    # Yellow → mint
    Color(165, 250, 65),
    Color(154, 246, 70),
    Color(143, 242, 75),
    Color(132, 238, 80),
    Color(121, 234, 85),
    Color(110, 230, 90),
    Color(99, 226, 95),
    Color(88, 222, 100),
    Color(77, 218, 105),
    Color(66, 214, 110),
    # Vibrant mint / green
    Color(55, 218, 125),
    Color(52, 222, 140),
    Color(49, 226, 155),
    Color(46, 230, 170),
    Color(43, 234, 185),
    Color(40, 238, 200),
    Color(38, 242, 215),
    Color(36, 246, 230),
    Color(34, 250, 240),
    Color(32, 252, 248),
    # Mint → cyan
    Color(30, 246, 250),
    Color(28, 238, 250),
    Color(26, 230, 250),
    Color(24, 222, 250),
    Color(22, 214, 250),
    Color(20, 206, 250),
    Color(18, 198, 250),
    Color(16, 190, 250),
    Color(14, 182, 250),
    Color(12, 174, 250),
    # Vibrant cyan / blue
    Color(10, 168, 250),
    Color(10, 158, 250),
    Color(10, 148, 250),
    Color(10, 138, 250),
    Color(10, 128, 250),
    Color(10, 118, 250),
    Color(10, 108, 250),
    Color(10, 98, 250),
    Color(10, 88, 250),
    Color(10, 78, 250),
    # Blue → lavender
    Color(18, 72, 250),
    Color(28, 68, 250),
    Color(38, 64, 250),
    Color(48, 60, 250),
    Color(58, 56, 250),
    Color(68, 52, 250),
    Color(78, 48, 250),
    Color(88, 44, 250),
    Color(98, 40, 250),
    Color(108, 36, 250),
    # Vibrant lavender
    Color(120, 38, 250),
    Color(132, 40, 250),
    Color(144, 42, 250),
    Color(156, 44, 250),
    Color(168, 46, 250),
    Color(180, 48, 250),
    Color(192, 50, 250),
    Color(204, 52, 250),
    Color(216, 54, 250),
    Color(228, 56, 250),
    # Lavender → pink
    Color(235, 58, 244),
    Color(238, 60, 232),
    Color(240, 62, 220),
    Color(242, 64, 208),
    Color(244, 66, 196),
    Color(246, 68, 184),
    Color(248, 70, 172),
    Color(250, 72, 160),
    Color(252, 74, 148),
    Color(255, 76, 136),
    # Back toward vibrant pink
    Color(255, 82, 142),
    Color(255, 88, 148),
    Color(255, 94, 154),
    Color(255, 100, 160),
    Color(255, 106, 166),
    Color(255, 112, 172),
    Color(255, 118, 178),
    Color(255, 124, 184),
    Color(255, 130, 190),
    Color(255, 136, 196),
]


# there are 2 types of animations
# 1. event based -> something happens and current animation is overridden
# 2. Ambient animation -> just goes on and on in the background
# animation switching and event reactions are based on proto threads
# so animation functions need
# 1. to store it's state internally
# 2. react to jumps in time
# 3. release execution control as soon as possible


class AnimationNode:
    def __init__(
        self,
        name: str,
        functionBody: str,
        description: str = "",
        proto_thread_timeout_ms: int = 1,
        is_active: bool = False,
    ):
        self.name = name
        self.description = description
        self.functionBody = functionBody
        self.proto_thread_timeout_ms = proto_thread_timeout_ms
        self.is_active = is_active

    def save_to_dict(self):
        
        return {
            "name": self.name,
            "description": self.description,
            "functionBody": self.functionBody,
            "proto_thread_timeout_ms": self.proto_thread_timeout_ms,
            "is_active": self.is_active,
        }


class Settings:
    def __init__(self, hal_sensor_pin):
        self.iot_central_url: str = "http://192.168.1.14/v1/connect"
        self.brightness = 100
        self.lamp_on = hal_sensor_pin.value() == 0
        self.last_button_reading = hal_sensor_pin.value()
        self.is_connected_to_central = False
        self.animations = []



led_strip = LedStrip(30, 16)

hal_pwr = Pin(15, Pin.OUT, value=1)
hal_sensor_pin = Pin(14, Pin.IN, Pin.PULL_UP)

rtc = RTC()
app = App(hostname="ghost.local")
device_settings = Settings(hal_sensor_pin)


def get_operation_time(uptime: int):
    if uptime <= 0:
        return "<1min"

    if uptime < 60:
        return f"{uptime}min"

    if uptime < 24 * 60:
        return f"{uptime // 60}h {uptime%60}min"

    return f"{(uptime // (24 * 60))}days {(uptime % (24 * 60)) // 60}h {floor(uptime%60)}min"


def hexify(num):
    return f"{num:02x}"


def get_hex_color(color: Color):
    return "#" + ("".join(hexify(value) for value in color.to_tuple()))


def datetime_diff_seconds(timestamp_a, timestamp_b):

    t1 = utime.mktime(timestamp_a)
    t2 = utime.mktime(timestamp_b)
    return t1 - t2


def home_page(cl: socket.socket, parameters: dict):
    cl.sendall(
        compose_response(
            response=format_dict(
                load_html("static/index.html"),
                {
                    "brightness": device_settings.brightness,
                    "iot_central_url": device_settings.iot_central_url,
                    "is_connected_to_iot_central": device_settings.is_connected_to_central,
                    "uptime": get_operation_time(
                        datetime_diff_seconds(app.server_start_time, utime.localtime())
                        / 60
                    ),
                },
            ),
            content_type="text/html; charset=utf-8",
        )
    )


def edit_animation(cl: socket.socket, parameters: dict):
    global device_settings

    name = parameters.get("name", None)
    functionBody = parameters.get("functionBody", None)
    proto_thread_timeout_ms = parameters.get("proto_thread_timeout_ms", None)

    if name == None or functionBody == None or proto_thread_timeout_ms == None:
        cl.sendall(
            compose_response(400, response="Missing one or more required parameter")
        )
        return

    description = parameters.get("description", None)
    is_active = parameters.get("is_active", None)


def save_settings(cl: socket.socket, parameters: dict):
    print(parameters)
    global device_settings

    device_settings.brightness = int(parameters.get("brightness", 100))
    iot_central_url = int(parameters.get("iot_central_url", iot_central_url))

    cl.sendall(compose_response())


def refresh_connection_to_central() -> bool:
    global device_settings
    try:
        res = requests.get(
            url=f"{device_settings.iot_central_url}?host_name={app.hostname}&ip={app.ip}&redirect_endpoint=/v1/toggle_lamp",
            timeout=10,
        )
        res.close()
        gc.collect()
        device_settings.is_connected_to_central = True

        return True
    except Exception as err:
        device_settings.is_connected_to_central = False
        print("Error occurred when connecting to IoT local")
        print(f"error:{str(err)}")
        return False


def synch_time(rtc, timezone_offset=1):
    try:
        ntptime.settime()

        t = time.time() + (60 * (60 * timezone_offset))
        tm = time.localtime(t)

        rtc.datetime(
            (tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0)  # weekday (1–7)
        )
    except (KeyboardInterrupt, Exception) as ex:
        print("ntptime error")


def measure_button():
    reading = hal_sensor_pin.value()
    global last_button_reading
    global lamp_on
    if last_button_reading != reading:
        lamp_on = reading == 0
        last_button_reading = reading


animation: str = "vibrant_colors"


def change_animation():
    pass


def animation():
    global animation
    offset = 0
    c = 0
    while 1 < 2:
        for _ in range(10 * 60 * 5):
            measure_button()

            if lamp_on:
                led_strip.brightness(brightness)
                if offset % 2 == 0:
                    c += 1

                for l in range(30):

                    led_strip.set_pixel(
                        l,
                        vibrant_colors[(l + c) % len(vibrant_colors)],
                        show=False,
                    )

                offset += 1
                led_strip.show()
            else:
                led_strip.fill(Color.black())

            time.sleep(0.1)
        refresh_connection_to_central()


top_pixels = range(0, 10, 1)
mid_pixels = range(10, 26, 1)
bottom_pixels = range(26, 29, 1)


def candle():
    global animation
    offset = 0
    c = 0
    while 1 < 2:
        for _ in range(10 * 60 * 5):
            measure_button()

            if lamp_on:
                led_strip.brightness(brightness)
                if offset % 2 == 0:
                    c += 1

                for l in range(30):

                    led_strip.set_pixels(
                        top_pixels,
                        Color.black(),
                        show=False,
                    )

                    led_strip.set_pixels(
                        mid_pixels,
                        Color.orange(),
                        show=False,
                    )

                    led_strip.set_pixels(
                        bottom_pixels,
                        Color.red(),
                        show=False,
                    )

                offset += 1
                led_strip.show()
            else:
                led_strip.fill(Color.black())

            time.sleep(0.1)
        refresh_connection_to_central()


if __name__ == "__main__":

    synch_time(rtc)
    refresh_connection_to_central()

    random.seed(utime.localtime()[4] * 60 + utime.localtime()[5])
    _thread.start_new_thread(candle, ())

    app.register_endpoint("/v1", home_page)
    app.register_endpoint("/v1/save_settings", save_settings)

    try:
        app.main_loop()
    except (KeyboardInterrupt, Exception) as ex:
        print(f"Server error type: {type(ex)}\tmessage: {ex}\texiting")
