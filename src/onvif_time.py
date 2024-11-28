import onvif
import ntplib
import datetime
import pytz
import json
import os


def current_time(host: str, port: str, timeout: int, tz: str):
    ntp_client = ntplib.NTPClient()
    ntp_response = ntp_client.request(host, version=3, port=port, timeout=timeout)
    timezone = pytz.timezone(tz)
    dt = datetime.datetime.fromtimestamp(ntp_response.tx_time, timezone)

    return dt


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
    print("Start:    local time -", datetime.datetime.now())

    CONFIG_FILE = os.environ.get("ONVIF_TIME_CONFIG", "/config/config.json")
    DRY_RUN = os.environ.get("ONVIF_TIME_DRY_RUN", "false").lower() == "true"
    TZ = os.environ.get("TZ", "UTC")

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except Exception as e:
        print("ERROR:    open configuration file - ", e)
        return

    NTP = config.get("ntp", {})
    NTP_HOST = NTP.get("host", "1.opnsense.pool.ntp.org")
    NTP_PORT = NTP.get("port", "ntp")
    NTP_TIMEOUT = NTP.get("timeout", 5)

    CAMERAS = config.get("cameras", {})

    try:
        dt = current_time(NTP_HOST, NTP_PORT, NTP_TIMEOUT, TZ)
        print(f"Success:  get time from NTP server {NTP_HOST} -", dt)
    except Exception as e:
        print(f"ERROR:    get time from NTP server {NTP_HOST} -", e)
        return

    for name, camera in CAMERAS.items():
        try:
            camera_host = camera["host"]
            camera_port = camera["port"]
            camera_user = camera["user"]
            camera_pass = camera["password"]

            set_camera_time(
                dt, camera_host, camera_port, camera_user, camera_pass, DRY_RUN
            )
            print(f"Success:  set time on camera {name}")
        except Exception as e:
            print(f"ERROR:    set time on camera {name} -", e)
            return


if __name__ == "__main__":
    main()
