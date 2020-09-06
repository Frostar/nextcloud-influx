#! /usr/bin/env python3
import logging
import sys

import requests
import sdnotify
from time import sleep, localtime, strftime
from dynaconf import LazySettings, Validator
from influxdb import InfluxDBClient

settings = LazySettings(
    SETTINGS_FILE_FOR_DYNACONF="default.toml,user.toml",
    ENVVAR_PREFIX_FOR_DYNACONF="NEXTCLOUD",
)
settings.validators.register(Validator("INSTANCES", must_exist=True))
settings.validators.validate()

n = sdnotify.SystemdNotifier()

logger = logging.getLogger()


class NextCloud:
    """Container object for a single Nextcloud instance."""

    def __init__(self, name, user, password, url):
        self.name = name
        self.user = user
        self.password = password
        self.url = url
        self.timeout = settings.as_int("REQUEST_TIMEOUT")
        self.logger = logging.getLogger("nextcloud." + name)
        self.logger.info("Initialized for %s (%s)", name, url)

        self.verify_ssl = settings.as_bool("REQUEST_VERIFY_SSL")
        if not self.verify_ssl:
            self.logger.warning("Disabled SSL verification for Nextcloud requests")

        if logger.level <= logging.INFO:
            data = self.get_data()
            keys = ", ".join(data.keys())
            self.logger.info("Found keys {}.".format(keys, ))

    def get_data(self):
        """Retrieve API data from Nextcloud serverinfo, and return as dict on success."""
        response = requests.get(self.url + "?format=json", auth=(self.user, self.password), timeout=self.timeout,
                                verify=self.verify_ssl)
        if response.status_code == 200:
            self.logger.debug("Got %d bytes", len(response.content))
            return self.format_payload(response.json())
        else:
            self.logger.error(
                "Got unexpected response %d, %s", response.status_code, response.content
            )

    @staticmethod
    def format_payload(raw_response_data):
        out = {}

        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + '.')
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + '.')
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(raw_response_data["ocs"]["data"])
        return out


class Daemon(object):
    def __init__(self, single_run=False):
        self.influx = InfluxDBClient(
            host=settings.INFLUXDB_HOST,
            port=settings.as_int("INFLUXDB_PORT"),
            username=settings.get("INFLUXDB_USERNAME"),
            password=settings.get("INFLUXDB_PASSWORD"),
            database=settings.INFLUXDB_DATABASE,
            ssl=settings.as_bool("INFLUXDB_SSL"),
            verify_ssl=settings.as_bool("INFLUXDB_VERIFY_SSL"),
        )
        self.single_run = single_run

        if "; " in settings.INSTANCES:
            name, user, password, url = settings.INSTANCES.split("; ")
            self.instances = [NextCloud(name, user, password, url)]
        else:
            raise ValueError("Unable to parse instances definition(s).")

    def run(self):
        logger.info("Running daemon, reporting to InfluxDB at %s.", self.influx._host)
        while True:
            for instance in self.instances:
                data = instance.get_data()
                self.send_msg(data, instance.name)
            timestamp = strftime("%Y-%m-%d %H:%M:%S %z", localtime())

            n.notify("STATUS=Last report to InfluxDB at {}".format(timestamp))
            n.notify("READY=1")
            if self.single_run:
                logger.info("Finished single run.")
                break
            sleep(settings.as_int("REPORTING_INTERVAL"))  # pragma: no cover

    def send_msg(self, resp, name):
        json_body = [{"measurement": "nextcloud", "tags": {"host": name}, "fields": resp}]

        self.influx.write_points(json_body)


def main(single_run=False):
    log_level = (settings.LOG_LEVEL).upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(levelname)s: [%(name)s] %(message)s",
    )

    daemon = Daemon(single_run)

    try:
        daemon.run()
    except KeyboardInterrupt:
        sys.exit(0)  # pragma: no cover
    except Exception:
        logger.exception("Unexpected exception", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
