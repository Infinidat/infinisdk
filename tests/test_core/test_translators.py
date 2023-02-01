from infinisdk.core.translators_and_types import SecondsDeltaTranslator, SecondsDatetimeTranslator
from datetime import timedelta
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
