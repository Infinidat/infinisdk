import sys
import pkg_resources
import click
import logbook
from infinisdk.infinibox import InfiniBox
from infinisdk.core.config import config


_logger = logbook.Logger('sdk-cli')
logbook.set_datetime_format('local')

_DEFAULT_CONSOLE_LEVEL = logbook.INFO

CUSTOMIZE_ENTRY_POINT = 'infinisdk.cli.customize'


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet", count=True)
@click.pass_context
def cli(ctx, verbose, quiet):
    console_handler = logbook.StderrHandler()
    console_handler.level = min(max(logbook.TRACE, _DEFAULT_CONSOLE_LEVEL-verbose+quiet), logbook.CRITICAL)
    ctx.obj['console_handler'] = console_handler
    console_handler.format_string = '{record.message}'
    console_handler.push_application()


def _get_system_object(system_name):
    system = InfiniBox(system_name)
    if not system.api.get_auth():
        _logger.warning("Auth (username & password) wasn't set. Set them by creating ini file in {}",
                        config.root.ini_file_path)
    return system

def _interact(**local_vars):
    try:
        from IPython import embed
        embed(user_ns=local_vars, display_banner=False)
    except ImportError:
        from code import interact
        interact(local=local_vars)


@cli.command()
@click.option("-s", "--system-name", required=True)
def interact(system_name):
    system = _get_system_object(system_name)
    if not system.api.get_auth():
        _logger.warning("Auth (username & password) wasn't set. Set them by creating ini file in {}",
                        config.root.ini_file_path)
    _interact(system=system)


def main_entry_point():
    for customize_function_cli in pkg_resources.iter_entry_points(CUSTOMIZE_ENTRY_POINT): # pylint: disable=no-member
        func = customize_function_cli.load()
        func()
    return cli(obj={})  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg


if __name__ == '__main__':
    sys.exit(main_entry_point())
