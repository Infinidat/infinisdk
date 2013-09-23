#!/usr/bin/env python
import argparse
import ast
import logging
import sys
import requests
import os
import yaml
from urlobject import URLObject
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tests.utils.api_scenarios import iter_api_scenario, get_real_scenario_filename

parser = argparse.ArgumentParser(usage="%(prog)s [options] system [scenario1 [scenario2 ...]]")
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
        filename = get_real_scenario_filename(filename)
        output_filename = filename + ".output"
        mementos = []
        for rule in iter_api_scenario(filename):
            result = rule.request.send(self.url, auth=self.auth)
            memento = rule.original_yaml
            memento["response"] = {"status_code": result.status_code, "json": result.json()}
            mementos.append(memento)
        with open(output_filename, "w") as outfile:
            outfile.write(
                yaml.safe_dump_all(
                    mementos,
                    encoding="utf-8",
                ))
        os.rename(output_filename, filename)

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
