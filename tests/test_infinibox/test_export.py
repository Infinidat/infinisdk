# pylint: disable=unused-argument
import pytest
from ..conftest import create_export
from infinisdk.infinibox.export import Export


def test_get_filesystem(infinibox, filesystem, export):
    assert export.get_filesystem() == filesystem


@pytest.mark.parametrize('field', Export.FIELDS)
def test_verify_fields(infinibox, export, field):
    if not infinibox.compat.is_feature_supported(field.feature_name):
        pytest.skip('System does not support {}'.format(field.feature_name))
    assert field.name == export.fields.get(field.name).name
    assert export.get_field(field.name) is not None

def test_create_export_with_filesystem_name(infinibox, filesystem):
    export = create_export(infinibox, filesystem=filesystem.get_name())
    assert export.get_filesystem() == filesystem
