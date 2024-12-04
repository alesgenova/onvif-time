import onvif
import ntplib
import datetime
import pytz
import json
import os


def get_ntp_response(host: str, port: str, timeout: int):
    ntp_client = ntplib.NTPClient()
    ntp_response = ntp_client.request(host, version=3, port=port, timeout=timeout)

    return ntp_response


def adjusted_now(timezone, offset: float) -> datetime.datetime:
    return datetime.datetime.now(tz=timezone) + datetime.timedelta(seconds=offset)


def round_seconds(t: datetime.datetime) -> datetime.datetime:
    if t.microsecond >= 500_000:
        t += datetime.timedelta(seconds=1)

    return t.replace(microsecond=0)


def set_camera_time(
    dt: datetime.datetime, host: str, port: int, user: str, password: str, dry: bool
):
    camera = onvif.ONVIFCamera(host, port, user, password)
    time_params = camera.devicemgmt.create_type("SetSystemDateAndTime")

    time_params.DateTimeType = "Manual"
    time_params.DaylightSavings = True if dt.dst() else False

    time_params.TimeZone = {"TZ": dt.tzname()}

    date = {
        "Year": dt.year,
        "Month": dt.month,
        "Day": dt.day,
    }

    time = {
        "Hour": dt.hour,
        "Minute": dt.minute,
        "Second": dt.second,
    }

    time_params.UTCDateTime = {"Date": date, "Time": time}

    if not dry:
        camera.devicemgmt.SetSystemDateAndTime(time_params)


def main():
    print("Info:     local time :", datetime.datetime.now())
    CONFIG_FILE = os.environ.get("ONVIF_TIME_CONFIG", "/config/config.json")
    DRY_RUN = os.environ.get("ONVIF_TIME_DRY_RUN", "false").lower() == "true"
    TZ = os.environ.get("TZ", "UTC")

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except Exception as e:
        print("ERROR:    open configuration file :", e)
        return

    NTP = config.get("ntp", None)

    offset = 0

    if NTP is not None:
        try:
            NTP_HOST = NTP.get("host", "pool.ntp.org")
            NTP_PORT = NTP.get("port", "ntp")
            NTP_TIMEOUT = NTP.get("timeout", 5)
            ntp_response = get_ntp_response(NTP_HOST, NTP_PORT, NTP_TIMEOUT)
            offset = ntp_response.offset
            print(f"Success:  get offset from NTP server {NTP_HOST} :", offset)
        except Exception as e:
            print(f"ERROR:    get offset from NTP server :", e)

    if offset == 0:
        print(f"Info:     using un-adjusted local time")

    CAMERAS = config.get("cameras", {})

    timezone = pytz.timezone(TZ)

    for name, camera in CAMERAS.items():
        try:
            t = round_seconds(adjusted_now(timezone, offset))

            camera_host = camera["host"]
            camera_port = camera["port"]
            camera_user = camera["user"]
            camera_pass = camera["password"]

            set_camera_time(
                t, camera_host, camera_port, camera_user, camera_pass, DRY_RUN
            )
            print(f"Success:  set time on camera {name} :", t)
        except Exception as e:
            print(f"ERROR:    set time on camera {name} :", e)
            continue


if __name__ == "__main__":
    main()
