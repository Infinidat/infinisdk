# pylint: disable=unused-argument
import pytest
from ..conftest import relevant_from_version, create_export
from infinisdk.infinibox.export import Export


@relevant_from_version('2.2')
def test_get_filesystem(infinibox, filesystem, export):
    assert export.get_filesystem() == filesystem


@relevant_from_version('2.2')
@pytest.mark.parametrize('field', Export.FIELDS)
def test_verify_fields(export, field):
    assert field.name == export.fields.get(field.name).name
    assert export.get_field(field.name) is not None

@relevant_from_version('2.2')
def test_create_export_with_filesystem_name(infinibox, filesystem):
    export = create_export(infinibox, filesystem=filesystem.get_name())
    assert export.get_filesystem() == filesystem
