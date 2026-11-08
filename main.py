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
iot_central_url: str = "http://192.168.1.14/v1/connect"
rtc = RTC()

single_color_value = Color.white()
brightness = 100

lamp_on = hal_sensor_pin.value() == 0

last_button_reading = hal_sensor_pin.value()
is_connected_to_central = False


def day_sun_cycle(elapsed_intervals, props={"cache": {}}):
    if elapsed_intervals < 30:
        return elapsed_intervals

    def tuple_to_seconds(time: tuple):
        return time[0] * 60 * 60 + time[1] * 60 + time[2]

    def parse_time(time_str: str):
        # hour minute second
        time_tuple = tuple(map(int, time_str.split(":")))
        return tuple_to_seconds(time_tuple)

    current_time = utime.localtime()
    # current day of the month
    data = {}
    if current_time[2] in props["cache"].keys():
        data = props["cache"][current_time[2]]
        print("loading cache")
    else:
        resp = requests.get(
            "https://api.sunrisesunset.io/json?lat=51.75201840666799&lng=51.75201840666799&time_format=24&formatted=0"
        )
        print("pulling data")
        r = resp.json()["results"]

        data = [
            # First visible signs of daylight before sunrise.
            # Sky begins to brighten; the Sun is still below the horizon.
            # "first_light":
            parse_time(r["first_light"]),
            # Beginning of astronomical/nautical transition toward daylight.
            # Sun is below the horizon; sky appears very dark blue.
            # "nautical_twilight_begin":
            parse_time(r["nautical_twilight_begin"]),
            # Morning blue hour: diffuse blue light before sunrise.
            # Sun is below the horizon; sky appears deep blue or cyan.
            # "blue_hour_morning_begin":
            parse_time(r["blue_hour_morning"]["begin"]),
            # End of morning blue hour.
            # Sky transitions from deep blue to lighter blue and warm dawn colors.
            # "blue_hour_morning_end":
            parse_time(r["blue_hour_morning"]["end"]),
            # Dawn: the sky becomes noticeably brighter before sunrise.
            # Sun is below the horizon; sky may appear orange, pink, or pale blue.
            # "dawn":
            parse_time(r["dawn"]),
            # Sunrise: the Sun crosses the horizon.
            # Sun typically appears orange, red, or golden due to atmospheric scattering.
            # "sunrise":
            parse_time(r["sunrise"]),
            # Morning golden hour: warm, soft sunlight shortly after sunrise.
            # Sun appears golden yellow, orange, or amber.
            # "golden_hour":
            parse_time(r["golden_hour"]),
            # Solar noon: Sun reaches its highest position in the sky.
            # Sun appears bright white or pale yellow, depending on atmospheric conditions.
            # "solar_noon":
            parse_time(r["solar_noon"]),
            # Evening golden hour begins: sunlight becomes warm and directional.
            # Sun appears golden yellow, orange, or amber.
            # "golden_hour_evening_begin":
            parse_time(r["golden_hour_evening"]["begin"]),
            # Evening golden hour ends: the Sun approaches the horizon.
            # Sunlight becomes increasingly orange, red, and warm.
            # "golden_hour_evening_end":
            parse_time(r["golden_hour_evening"]["end"]),
            # Dusk: the Sun has set, but some daylight remains.
            # Sun is below the horizon; sky often appears orange, pink, or purple.
            # "dusk":
            parse_time(r["dusk"]),
            # Evening blue hour begins: twilight transitions into deep blue tones.
            # Sun is below the horizon; sky appears blue, indigo, or violet.
            # "blue_hour_evening_begin":
            parse_time(r["blue_hour_evening"]["begin"]),
            # Evening blue hour ends: the sky becomes significantly darker.
            # Sun is below the horizon; sky transitions to dark navy blue.
            # "blue_hour_evening_end":
            parse_time(r["blue_hour_evening"]["end"]),
            # End of nautical twilight: the sky is becoming fully dark.
            # Sun is well below the horizon; sky appears dark blue or nearly black.
            # "nautical_twilight_end":
            parse_time(r["nautical_twilight_end"]),
            # Moonrise: the Moon crosses the horizon.
            # Moon often appears orange or yellow near the horizon, becoming white or pale gray higher up.
            # "moonrise":
            # parse_time(r["moonrise"]),
            # Moonset: the Moon disappears below the horizon.
            # Moon may appear yellow, orange, or reddish near the horizon.
            # "moonset":
            # parse_time(r["moonset"]),
        ]
        props["cache"][current_time[2]] = data

    # hour minute second
    current_time = tuple_to_seconds((current_time[3], current_time[4], current_time[5]))

    id = 0
    for i in data:
        if i > current_time:
            break
        else:
            id += 1

    sun_step_colors = [
        # Morning
        # "first_light":
        Color(35, 45, 90),  # Deep twilight blue
        # "nautical_twilight_begin":
        Color(20, 30, 75),  # Dark navy blue
        # "blue_hour_morning_begin":
        Color(35, 65, 150),  # Deep blue
        # "blue_hour_morning_end":
        Color(75, 130, 210),  # Soft sky blue
        # "dawn":
        Color(255, 115, 75),  # Warm coral orange
        # "sunrise":
        Color(255, 85, 35),  # Sunrise orange-red
        # "golden_hour":
        Color(255, 175, 65),  # Golden amber
        # Daytime
        # "solar_noon":
        Color(255, 245, 215),  # Warm daylight white
        # Evening
        # "golden_hour_evening_begin":
        Color(255, 185, 85),  # Golden yellow
        # "golden_hour_evening_end":
        Color(255, 105, 45),  # Deep sunset orange
        # "dusk":
        Color(185, 75, 115),  # Dusky pink
        # "blue_hour_evening_begin":
        Color(75, 90, 185),  # Twilight blue
        # "blue_hour_evening_end":
        Color(30, 45, 115),  # Deep indigo
        # "nautical_twilight_end":
        Color(12, 18, 45),  # Midnight navy
        # Moon
        # "moonrise": Color(210, 195, 155),  # Warm moonlight
        # "moonset": Color(175, 155, 135),  # Fading warm moonlight
    ]

    if id >= len(sun_step_colors):
        id = len(sun_step_colors) - 1

    led_strip.fill(sun_step_colors[id])


def off_animation(elapsed_intervals):
    led_strip.fill(Color.black())


def single_color_animation(elapsed_intervals):
    if elapsed_intervals < 10:
        return elapsed_intervals
    global single_color_value
    led_strip.brightness(brightness, show=False)
    led_strip.fill(single_color_value)


def spiral_animation(elapsed_intervals, static_variables={"offset": 0, "c": 0}):

    if static_variables["offset"] % 2 == 0:
        static_variables["c"] += 1

    for l in range(30):
        led_strip.set_pixel(
            l,
            vibrant_colors[(l + static_variables["c"]) % len(vibrant_colors)],
            show=False,
        )

    static_variables["offset"] += 1
    led_strip.brightness(brightness)


ANIMATIONS = {
    "day_cycle_animation": {
        "animation": day_sun_cycle,
        "last_activation": (2026, 1, 1, 0, 0, 0, 0, 0),
    },
    "single_color": {
        "animation": single_color_animation,
        "last_activation": (2026, 1, 1, 0, 0, 0, 0, 0),
    },
    "spiral": {
        "animation": spiral_animation,
        "last_activation": (2026, 1, 1, 0, 0, 0, 0, 0),
    },
    "off": {
        "animation": off_animation,
        "last_activation": (2026, 1, 1, 0, 0, 0, 0, 0),
    },
}


ROUTINE = [
    # {timestamp, }
]

follow_routine: bool = False
selected_animation: str = "day_cycle_animation"


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
                    "single_color_value": get_hex_color(single_color_value),
                    "brightness": brightness,
                    "iot_central_url": iot_central_url,
                    "uptime": get_operation_time(
                        datetime_diff_seconds(app.server_start_time, utime.localtime())
                        / 60
                    ),
                },
            ),
            content_type="text/html; charset=utf-8",
        )
    )


def toggle_lamp(cl: socket.socket, parameters: dict):
    #
    pass


def get_hex_color(color: Color):
    return "#" + ("".join(hexify(value) for value in color.to_tuple()))


def save_settings(cl: socket.socket, parameters: dict):

    global brightness
    global iot_central_url
    global selected_animation
    global single_color_value

    brightness = int(parameters.get("brightness", 100))
    iot_central_url = str(parameters.get("iot_central_url", iot_central_url))
    selected_animation = str(parameters.get("selected_animation", selected_animation))

    if selected_animation == "single_color":
        new_color_str = parameters.get("param1", get_hex_color(single_color_value))

        single_color_value = Color(
            *tuple(int(new_color_str[i : i + 2], 16) for i in (0, 2, 4))
        )

    cl.sendall(compose_response(response="ok"))


def refresh_connection_to_central() -> bool:
    global is_connected_to_central
    try:
        res = requests.get(
            url=f"{iot_central_url}?host_name={app.hostname}&ip={app.ip}&redirect_endpoint=/v1/toggle_lamp",
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


def animation_thread():
    global selected_animation
    intervals = 1000
    while 1 < 2:
        for _ in range(10 * 60 * 5):
            # button simply turns animation off
            measure_button()
            if lamp_on:

                # t_diff = datetime_diff_seconds(
                #     utime.localtime(), ANIMATIONS["spiral"]["last_activation"]
                # )

                intervals = ANIMATIONS[selected_animation]["animation"](intervals)
                if intervals == None:
                    intervals = 0
                else:
                    intervals += 1
            else:
                led_strip.fill(Color.black())

            time.sleep(0.1)
        refresh_connection_to_central()


if __name__ == "__main__":

    synch_time(rtc)
    random.seed(utime.localtime()[4] * 60 + utime.localtime()[5])
    _thread.start_new_thread(animation_thread, ())

    app.register_endpoint("/v1", home_page)
    app.register_endpoint("/v1/save_settings", save_settings)
    app.register_endpoint("/v1/toggle_lamp", toggle_lamp)

    try:
        app.main_loop()
    except (KeyboardInterrupt, Exception) as ex:
        print(f"Server error type: {type(ex)}\tmessage: {ex}\texiting")
