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
    while 1 < 2:
        for _ in range(10 * 60 * 5):

            if hal_sensor_pin.value() == 0:
                color = sun_colors[6]
                led_strip.brightness(100)
                led_strip.fill(Color.gold())
                # for l in range(30):
                #     # for c in range(len(Color.colors())):

                #     led_strip.set_pixel(
                #         l,
                #         sun_colors[(l + offset) % len(sun_colors)],
                #         show=False,
                #     )

                # offset += 1
                # led_strip.show()
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
