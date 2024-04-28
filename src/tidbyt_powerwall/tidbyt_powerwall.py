#!/usr/bin/env python3
"""Tidbyt custom app to display Tesla Powerwall status"""

import base64
import io
import os
import time
import typing as t
from datetime import datetime
from importlib.resources import files

import requests
from PIL import Image, ImageDraw, ImageFont
from tesla_powerwall import Powerwall  # type: ignore[import-untyped]
from urllib3.util.retry import Retry

if t.TYPE_CHECKING:
    from requests.sessions import _Data


__version__ = "1.0.0"


class Tidbyt:  # pylint:disable=too-few-public-methods
    """interface to Tidbyt API"""

    def __init__(self, device_id: str, api_key: str):
        self.device_id = device_id
        self.api_key = api_key
        req_retry_strategy = Retry(total=5, backoff_factor=1)
        self._requests_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=req_retry_strategy)
        self._requests_session.mount("http://", adapter)
        self._requests_session.mount("https://", adapter)

    def _request(
        self,
        method: str,
        url: str,
        params: t.Optional[t.Dict[str, str]] = None,
        data: "t.Optional[_Data]" = None,
    ) -> requests.Response | None:
        """perform an HTTP request and return a requests.Response object"""
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }
        params = {} if params is None else params
        try:
            response = self._requests_session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=5,
            )
        except requests.exceptions.ReadTimeout:
            return None
        return response

    def push(self, image_bytes: io.BytesIO, installation_id: str, background: bool) -> requests.Response | None:
        """push an image to Tidbyt

        :param image: a 64x32 PNG, WebP, or GIF, animation is supported
        :param installation_id: if provided, the image will update a specific installation
               in the device's rotation, if it doesn't exist it will be created
        :param background:

        ref.: https://tidbyt.dev/docs/tidbyt-api/b3A6MTYyODkwOA-push-to-a-device
        """
        url = f"https://api.tidbyt.com/v0/devices/{self.device_id}/push"
        image_data = image_bytes.getvalue()
        data = {
            "image": base64.b64encode(image_data).decode(),
            "installationID": installation_id,
            "background": background,
        }
        response = self._request(method="POST", url=url, data=data)
        return response


class TidbytScreen:
    """image renderer for Tidbyt Screen"""

    # RGB values
    RED = (200, 0, 0)
    ORANGE = (200, 200, 0)
    GREEN = (0, 200, 0)
    BLUE = (0, 0, 255)
    LIGHT_BLUE = (100, 100, 255)
    LIGHT_BLUE_2 = (80, 80, 200)
    GRAY = (165, 165, 165)
    WHITE = (255, 255, 255)

    def __init__(self) -> None:
        # try to load fonts from an actually installed module
        try:
            fonts = files("tidbyt_powerwall.fonts")
            fontfile_5x8 = str(fonts.joinpath("5x8.pil"))
            fontfile_tom = str(fonts.joinpath("tom-thumb.pil"))
        # if that fails, look for a fonts/ subdir where this script is located
        except ModuleNotFoundError:
            fontfile_5x8 = os.path.join(os.path.dirname(__file__), "fonts", "5x8.pil")
            fontfile_tom = os.path.join(os.path.dirname(__file__), "fonts", "tom-thumb.pil")
        self.font_5x8 = ImageFont.load(fontfile_5x8)
        self.font_tom = ImageFont.load(fontfile_tom)

    def compose_image(  # pylint:disable=too-many-arguments
        self,
        charge: int,
        battery_power: float,
        load_power: float,
        is_drawing: bool,
        is_charging: bool,
        now: datetime | None = None,
    ) -> Image.Image:
        """compose and return an Image"""
        now = now or datetime.now()
        # choose message and colors
        if charge <= 5:
            charge_color = self.RED
        elif charge <= 50:
            charge_color = self.ORANGE
        else:
            charge_color = self.GREEN
        if is_drawing:
            battery_msg = f"out {abs(battery_power):3.1f}kW"
            battery_color = self.RED
        elif is_charging:  #  -------------
            battery_msg = f" in {abs(battery_power):3.1f}kW"
            battery_color = self.GREEN
        else:
            battery_msg = "  standby"
            battery_color = self.BLUE
        # compose Image
        # ref.: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.multiline_text
        image = Image.new("RGB", (64, 32))
        draw = ImageDraw.Draw(image)
        # ROW 1: title and time of day
        draw.text(xy=(0, 1), text="PowerWall", fill=self.GRAY, font=self.font_tom)
        draw.text(xy=(40, 0), text=now.strftime("%H:%M"), fill=self.WHITE, font=self.font_5x8)
        # ROW 2: battery state of charge
        draw.text(
            xy=(0, 10),
            text="battery",
            fill=t.cast(tuple[int, int, int], tuple(map(lambda _: int(_ * 0.8), charge_color))),
            font=self.font_tom,
        )
        draw.text(xy=(30, 8), text=f"{charge:5.1f} %", fill=charge_color, font=self.font_5x8)
        # ROW 3: battery power flow (charge/discharge/standby)
        draw.text(
            xy=(0, 18),
            text="pwr",
            fill=t.cast(tuple[int, int, int], tuple(map(lambda _: int(_ * 0.8), battery_color))),
            font=self.font_tom,
        )
        draw.text(xy=(20, 16), text=battery_msg, fill=battery_color, font=self.font_5x8)  # 9 chars wide
        # ROW 4: household consumed power
        draw.text(xy=(0, 26), text="load", fill=self.LIGHT_BLUE_2, font=self.font_tom)
        draw.text(xy=(20, 24), text=f"{load_power:7.1f}kW", fill=self.LIGHT_BLUE, font=self.font_5x8)
        return image

    def compose_webp(  # pylint:disable=too-many-arguments
        self,
        charge: int,
        battery_power: float,
        load_power: float,
        is_drawing: bool,
        is_charging: bool,
        now: datetime,
    ) -> io.BytesIO:
        """compose an Image and return it in WebP format"""
        image = self.compose_image(charge, battery_power, load_power, is_drawing, is_charging, now)
        webp = io.BytesIO()
        # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp
        # save image to memory buffer
        image.save(webp, format="WebP", lossless=True, quality=100, method=6)
        webp.seek(0)
        return webp


def get_powerwall(endpoint: str, password: str) -> Powerwall:
    """return a logged-in Powerwall instance"""
    powerwall = Powerwall(endpoint=endpoint)
    powerwall.login(password=password)
    return powerwall


def main(sleep_interval: int = 60) -> t.NoReturn:
    """main loop"""
    powerwall = get_powerwall(endpoint=os.environ["TPW_ADDRESS"], password=os.environ["TPW_PASSWORD"])
    tidbyt = Tidbyt(device_id=os.environ["TPW_DEVICEID"], api_key=os.environ["TPW_APIKEY"])
    tidbyt_screen = TidbytScreen()
    while True:
        # get data from PowerWall
        now = datetime.now()
        charge = powerwall.get_charge()
        meters = powerwall.get_meters()
        battery_power = meters.battery.get_power()
        load_power = meters.load.get_power()
        # generate Image
        webp = tidbyt_screen.compose_webp(
            charge=charge,
            battery_power=battery_power,
            load_power=load_power,
            is_drawing=meters.battery.is_drawing_from(),
            is_charging=meters.battery.is_sending_to(),
            now=now,
        )
        # upload image to Tidbyt servers
        tidbyt.push(image_bytes=webp, installation_id="powerwall", background=True)
        # log and sleep until next round minute
        print(now.isoformat(), f"bat={battery_power:4.1f}kW load={load_power:3.1f}kW soc={charge:4.1f}%")
        sleep = sleep_interval - time.time() % sleep_interval
        time.sleep(sleep)


if __name__ == "__main__":
    main()
