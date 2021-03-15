# pylint: disable=unused-argument
import pytest
from ..conftest import create_share
from infinisdk.infinibox.share import Share


def test_get_filesystem(infinibox, filesystem, share):
    assert share.get_filesystem() == filesystem


@pytest.mark.parametrize('field', Share.FIELDS)
def test_verify_fields(infinibox, share, field):
    if not infinibox.compat.is_feature_supported(field.feature_name):
        pytest.skip('System does not support {}'.format(field.feature_name))
    assert field.name == share.fields.get(field.name).name
    assert share.get_field(field.name) is not None

def test_create_share_with_filesystem_name(infinibox, filesystem):
    share = create_share(infinibox, filesystem=filesystem.get_name())
    assert share.get_filesystem() == filesystem
