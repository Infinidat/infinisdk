import sys
import arrow
import dateutil
import pkg_resources
import click
import logbook
import logbook.more
from infinisdk import Q
from infinisdk.infinibox import InfiniBox
from infinisdk.core.config import config


_logger = logbook.Logger('sdk-cli')
logbook.set_datetime_format('local')

_DEFAULT_CONSOLE_LEVEL = logbook.INFO

CUSTOMIZE_ENTRY_POINT = 'infinisdk.cli.customize'


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet", count=True)
@click.option("-l", "--log-file", type=click.Path())
def cli(verbose, quiet, log_file):
    console_handler = logbook.more.ColorizedStderrHandler()
    console_handler.level = min(max(logbook.TRACE, _DEFAULT_CONSOLE_LEVEL-verbose+quiet), logbook.CRITICAL)
    console_handler.format_string = '{record.message}'
    console_handler.push_application()
    if log_file:
        file_handler = logbook.FileHandler(log_file, mode="w", bubble=True)
        file_handler.push_application()


def _get_system_object(system_name, port=None, should_login=False):
    address = system_name if port is None else (system_name, port)
    system = InfiniBox(address)
    has_auth = bool(system.api.get_auth())
    if not has_auth:
        msg = "Auth (username & password) wasn't set at {!r} file".format(config.root.ini_file_path)
        click.echo(click.style(msg, fg='yellow'))
    if should_login:
        if not has_auth:
            click.echo('Please provide authentication for your system')
            username = click.prompt('Username')
            password = click.prompt('Password', hide_input=True)
            system.api.set_auth(username, password=password, login=False)
        try:
            system.login()
        except Exception:
            _logger.debug('Caught exception while trying to login', exc_info=True)
            raise click.ClickException('Failed to login to system {}'.format(system_name))
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
@click.option("-p", "--port", type=int)
@click.option("--login", "should_login", is_flag=True, default=False)
def interact(system_name, port, should_login):
    system = _get_system_object(system_name, port=port, should_login=should_login)
    _interact(system=system)


@cli.group()
def events():
    pass

TIME_TEPMPLATE = 'YYYY-MM-DD HH:mm:ss'

def _convert_time_string_to_arrow(time_string, tzinfo):
    datetime_obj = dateutil.parser.parse(time_string)
    return arrow.get(datetime_obj, tzinfo=tzinfo)

@events.command(name='query')
@click.option("-s", "--system-name", required=True)
@click.option("--show-reporter/--hide-reporter", default=False, is_flag=True)
@click.option("--show-visibility/--hide-visibility", default=False, is_flag=True)
@click.option("--show-source-node-id/--hide-source-node-id", default=False, is_flag=True)
@click.option("--force-color/--no-color", "enable_color", default=None, is_flag=True)
@click.option("--local-time/--utc-time", "display_in_local_time", default=True, is_flag=True)
@click.option("-l", "--level", "min_level", default=None)
@click.option("-S", "--since", default=None)
@click.option("-U", "--until", default=None)
@click.option("--asc/--desc", "sorting_order", default=None, is_flag=True)
def events_query(system_name, show_reporter, show_visibility, show_source_node_id, display_in_local_time,
                 enable_color, min_level, since, until, sorting_order):
    tzinfo = 'local' if display_in_local_time else 'utc'
    if enable_color is None:
        enable_color = sys.stdout.isatty()
    if enable_color:
        colorize = {'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red', 'INFO': 'green'}.get
    else:
        colorize = lambda _: None
    system = _get_system_object(system_name, should_login=True)
    system.login()
    filters = []
    if min_level:
        supported_levels = system.events.get_levels()
        try:
            min_index = supported_levels.index(min_level)
        except ValueError:
            raise click.ClickException('Unsupported level {!r}'.format(min_level))
        filters.append(Q.level.in_(supported_levels[min_index:]))
    if since is not None:
        filters.append(Q.timestamp > _convert_time_string_to_arrow(since, tzinfo))
    if until is not None:
        filters.append(Q.timestamp < _convert_time_string_to_arrow(until, tzinfo))
    query = system.events.find(*filters)
    if sorting_order is not None:
        query = query.sort(+Q.id if sorting_order else -Q.id)
    for event in query:
        event_info = event.get_fields(from_cache=True)
        event_time = event_info['timestamp']
        if display_in_local_time:
            event_time = event_time.to('local')
        formatted = '{} {:5}'.format(event_time.format(TIME_TEPMPLATE), event_info['id'])
        if show_reporter:
            formatted += ' {:10}'.format(event_info['reporter'])
        if show_visibility:
            formatted += ' {:9}'.format(event['visibility'])
        if show_source_node_id:
            formatted += ' node-{}'.format(event['source_node_id'])
        click.echo(formatted+' ', nl=False)
        level = event_info['level']
        click.echo(click.style(level, fg=colorize(level)), nl=False)
        click.echo(' {code} {desc}'.format(code=event_info['code'], desc=event_info['description'].replace('\n', ' ')))


def main_entry_point():
    for customize_function_cli in pkg_resources.iter_entry_points(CUSTOMIZE_ENTRY_POINT): # pylint: disable=no-member
        func = customize_function_cli.load()
        func()
    return cli(obj={})  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg


if __name__ == '__main__':
    sys.exit(main_entry_point())
