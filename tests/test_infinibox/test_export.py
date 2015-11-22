# pylint: disable=unused-argument
import pytest
from ..conftest import new_to_version
from infinisdk.infinibox.export import Export


@new_to_version('2.2')
def test_get_filesystem(infinibox, filesystem, export):
    assert export.get_filesystem() == filesystem


@new_to_version('2.2')
@pytest.mark.parametrize('field', Export.FIELDS)
def test_verify_fields(export, field):
    assert field.name == export.fields.get(field.name).name
    assert export.get_field(field.name) is not None
