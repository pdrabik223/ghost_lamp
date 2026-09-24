from math import floor
import random
import time

import requests
from pi_pico_neopixel_tools.color import Color
from pi_pico_neopixel_tools.led_strip import LedStrip
from pi_pico_w_server_tools.app import *
import ntptime
from machine import Pin, RTC, ADC
import _thread

led_strip = LedStrip(30, 16)

hal_pwr = Pin(15, Pin.OUT, value=1)
hal_sensor_pin = Pin(14, Pin.IN, Pin.PULL_UP)

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
soft_colors = [
    # Soft pinks
    Color(255, 220, 230),
    Color(255, 216, 228),
    Color(255, 212, 226),
    Color(255, 208, 224),
    Color(255, 205, 222),
    Color(255, 202, 220),
    Color(255, 199, 218),
    Color(255, 196, 216),
    Color(255, 193, 214),
    Color(255, 190, 212),
    # Pink → peach
    Color(255, 190, 207),
    Color(255, 192, 203),
    Color(255, 194, 199),
    Color(255, 196, 195),
    Color(255, 198, 191),
    Color(255, 200, 187),
    Color(255, 202, 183),
    Color(255, 204, 179),
    Color(255, 206, 175),
    Color(255, 208, 171),
    # Soft peach / orange
    Color(255, 211, 176),
    Color(255, 214, 181),
    Color(255, 217, 186),
    Color(255, 220, 191),
    Color(255, 223, 196),
    Color(255, 226, 201),
    Color(255, 229, 206),
    Color(255, 232, 211),
    Color(255, 235, 216),
    Color(255, 238, 221),
    # Peach → yellow
    Color(255, 240, 215),
    Color(255, 242, 209),
    Color(255, 244, 203),
    Color(255, 246, 197),
    Color(255, 248, 191),
    Color(255, 250, 185),
    Color(255, 251, 179),
    Color(255, 252, 173),
    Color(255, 253, 167),
    Color(255, 254, 161),
    # Soft yellows
    Color(254, 255, 164),
    Color(250, 255, 167),
    Color(246, 255, 170),
    Color(242, 255, 173),
    Color(238, 255, 176),
    Color(234, 255, 179),
    Color(230, 255, 182),
    Color(226, 255, 185),
    Color(222, 255, 188),
    Color(218, 255, 191),
    # Yellow → mint
    Color(213, 250, 192),
    Color(208, 248, 194),
    Color(203, 246, 196),
    Color(198, 244, 198),
    Color(193, 242, 200),
    Color(188, 240, 202),
    Color(183, 238, 204),
    Color(178, 236, 206),
    Color(173, 234, 208),
    Color(168, 232, 210),
    # Soft mint / green
    Color(164, 232, 215),
    Color(164, 233, 220),
    Color(164, 234, 225),
    Color(164, 235, 230),
    Color(164, 236, 235),
    Color(165, 237, 240),
    Color(166, 238, 243),
    Color(168, 239, 246),
    Color(170, 240, 248),
    Color(172, 241, 250),
    # Mint → cyan
    Color(175, 239, 250),
    Color(178, 237, 250),
    Color(181, 235, 250),
    Color(184, 233, 250),
    Color(187, 231, 250),
    Color(190, 229, 250),
    Color(193, 227, 250),
    Color(196, 225, 250),
    Color(199, 223, 250),
    Color(202, 221, 250),
    # Soft cyan / blue
    Color(204, 220, 250),
    Color(205, 218, 250),
    Color(206, 216, 250),
    Color(207, 214, 250),
    Color(208, 212, 250),
    Color(209, 210, 250),
    Color(210, 208, 250),
    Color(211, 206, 250),
    Color(212, 204, 250),
    Color(213, 202, 250),
    # Blue → lavender
    Color(214, 201, 250),
    Color(216, 200, 250),
    Color(218, 199, 250),
    Color(220, 198, 250),
    Color(222, 197, 250),
    Color(224, 196, 250),
    Color(226, 195, 250),
    Color(228, 194, 250),
    Color(230, 193, 250),
    Color(232, 192, 250),
    # Soft lavender
    Color(234, 192, 250),
    Color(236, 193, 250),
    Color(238, 194, 250),
    Color(240, 195, 250),
    Color(242, 196, 250),
    Color(244, 197, 250),
    Color(246, 198, 250),
    Color(248, 199, 250),
    Color(250, 200, 250),
    Color(252, 201, 250),
    # Lavender → pink
    Color(252, 202, 247),
    Color(252, 203, 244),
    Color(252, 204, 241),
    Color(252, 205, 238),
    Color(252, 206, 235),
    Color(252, 207, 232),
    Color(252, 208, 229),
    Color(252, 209, 226),
    Color(252, 210, 223),
    Color(252, 211, 220),
    # Back toward soft pink
    Color(253, 212, 220),
    Color(253, 213, 221),
    Color(253, 214, 222),
    Color(253, 215, 223),
    Color(253, 216, 224),
    Color(253, 217, 225),
    Color(254, 218, 226),
    Color(254, 219, 227),
    Color(254, 220, 228),
    Color(255, 220, 230),
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


app = App(hostname="ghost.local")
central_url: str = "http://192.168.1.14/v1/connect"
rtc = RTC()


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
                    "uptime": get_operation_time(
                        datetime_diff_seconds(app.server_start_time, utime.localtime())
                        / 60
                    ),
                },
            )
        )
    )


is_connected_to_central = False


def refresh_connection_to_central() -> bool:
    global is_connected_to_central
    try:
        res = requests.get(
            url=f"{central_url}?host_name={app.hostname}&ip={app.ip}&redirect_endpoint=/v1/toggle_lamp",
            timeout=5,
        )
        res.close()
        gc.collect()
        is_connected_to_central = True

        return True
    except Exception as err:
        is_connected_to_central = False

        print(f"error:{str(err)}")
        return False


def synch_time(rtc, timezone_offset=1):
    ntptime.settime()

    t = time.time() + (60 * (60 * timezone_offset))
    tm = time.localtime(t)

    rtc.datetime(
        (tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0)  # weekday (1–7)
    )


def animation():

    offset = 0
    c = 0
    while 1 < 2:
        for _ in range(10 * 60 * 5):

            if hal_sensor_pin.value() == 0:

                led_strip.brightness(100)
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


if __name__ == "__main__":

    synch_time(rtc)
    random.seed(utime.localtime()[4] * 60 + utime.localtime()[5])
    _thread.start_new_thread(animation, ())

    app.register_endpoint("/v1", home_page)
    try:
        app.main_loop()
    except (KeyboardInterrupt, Exception) as ex:
        print(f"Server error type: {type(ex)}\tmessage: {ex}\texiting")
