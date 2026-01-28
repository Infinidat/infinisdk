from infinisdk.core.translators_and_types import SecondsDeltaTranslator, SecondsDatetimeTranslator, TimeOfDayTranslator
from datetime import timedelta, time
import arrow


def test_seconds_translator() -> None:
    translator = SecondsDeltaTranslator()
    # pylint: disable=protected-access
    assert translator._to_api(timedelta(seconds=10)) == 10
    assert translator._to_api(timedelta(seconds=10, days=2)) == (2*24*3600 + 10)
    assert translator._from_api(1500) == timedelta(seconds=1500)


def test_seconds_datetime_translator() -> None:
    # pylint: disable=protected-access
    translator = SecondsDatetimeTranslator()
    unix_time = 1675274123
    assert translator._from_api(unix_time) == arrow.Arrow(2023, 2, 1, 17, 55, 23)
    assert translator._to_api(arrow.Arrow(2023, 2, 1, 17, 55, 23)) == unix_time

def test_time_of_day_translator() -> None:
    # pylint: disable=protected-access
    translator = TimeOfDayTranslator()
    seconds_since_midnight = 90
    assert translator._from_api(seconds_since_midnight) == time(0, 1, 30)
    assert translator._to_api(time(1, 2, 3)) == (1*60*60 + 2*60 + 3)
    assert translator._from_api(translator._to_api(time(1, 2, 3))) == time(1, 2, 3)
    assert translator._from_api(None) is None
    assert translator._to_api(None) is None
