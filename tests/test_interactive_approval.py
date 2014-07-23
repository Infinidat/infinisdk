from contextlib import contextmanager
from infinisdk import _compat
from infinisdk.core.exceptions import CommandNotApproved

import pytest


def test_interactive_approval(infinibox, volume, interactive_approval):
    infinibox.api.set_interactive_approval()
    with interactive_approval.raises_context():
        volume.delete()


@pytest.fixture
def interactive_approval(request, approved):

    prev_raw_input = _compat.raw_input

    returned = InteractiveApproval()
    returned.approved = approved

    def fake_raw_input(msg):
        returned.msg = msg
        returned.asked = True
        if approved:
            return "y\n"
        return "n\n"

    _compat.raw_input = fake_raw_input

    @request.addfinalizer
    def cleanup():
        _compat = prev_raw_input

    return returned


class InteractiveApproval(object):

    asked = False

    @contextmanager
    def raises_context(self):
        if self.approved:
            yield
        else:
            with pytest.raises(CommandNotApproved):
                yield
        assert self.asked
        assert self.msg.endswith("Approve? [y/N] ")



@pytest.fixture(params=[True, False])
def approved(request):
    return request.param
