#!/usr/bin/env python
import argparse
import ast
import logging
import sys
import requests
import os
from urlobject import URLObject
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.utils.api_scenarios.utils import *

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("-v", action="append_const", const=1, dest="verbosity", default=[],
                    help="Be more verbose. Can be specified multiple times to increase verbosity further")
parser.add_argument("-u", "--username", default="Infinidat")
parser.add_argument("-p", "--password", default="123456")
parser.add_argument("system")
parser.add_argument("filenames", nargs="+")

class Application(object):
    def __init__(self, args):
        self._args = args
        self.auth = self._args.username, self._args.password
        self.url = URLObject("http://{}".format(self._args.system))

    def main(self):
        for filename in self._args.filenames:
            self.update_scenarios(filename)
        return 0

    def update_scenarios(self, filename):
        output_filename = filename + ".output"
        try:
            with open(filename, "r") as infile, open(output_filename, "w") as outfile:
                for chunk in self._iter_chunks(infile):
                    outfile.write(chunk)
        except:
            if os.path.isfile(output_filename):
                os.unlink(output_filename)
            raise
        os.rename(output_filename, filename)

    def _iter_chunks(self, infile):
        for line in infile:
            if "WHAT?" in line or "AUTOUPDATE" in line:
                line = self._translate_what(line)
            yield line

    def _translate_what(self, line):
        request_str = line.split(">>")[0].strip()
        request = eval(request_str)
        response = request.send(self.url, auth=self.auth)
        returned = "{} >> {} # AUTOUPDATE\n".format(request_str, self._format_response(response))
        logging.debug("%r --> %r", line, returned)
        return returned

    def _format_response(self, response):
        if response.status_code != 200:
            logging.debug("Bad status for request: %s (%s)", response.status_code, response.content)
        response.raise_for_status()
        assert response.headers["Content-type"] == "application/json"
        return "OK(JSON({}))".format(response.content.replace("true", "True").replace("false", "False"))

################################## Boilerplate ################################
def _configure_logging(args):
    verbosity_level = len(args.verbosity)
    if verbosity_level == 0:
        level = "WARNING"
    elif verbosity_level == 1:
        level = "INFO"
    else:
        level = "DEBUG"
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(asctime)s -- %(message)s"
        )

#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    _configure_logging(args)
    app = Application(args)
    sys.exit(app.main())

if __name__ == "__main__":
    main_entry_point()
