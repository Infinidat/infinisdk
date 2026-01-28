# pylint: disable=unused-argument
import pytest
from ..conftest import create_export
from infinisdk.infinibox.export import Export
from infinisdk.core.exceptions import APICommandFailed


def test_get_filesystem(infinibox, filesystem, export):
    assert export.get_filesystem() == filesystem


@pytest.mark.parametrize('field', Export.FIELDS)
def test_verify_fields(infinibox, export, field):
    if not infinibox.compat.is_feature_supported(field.feature_name):
        pytest.skip('System does not support {}'.format(field.feature_name))
    fields_with_initial_none = {
            "nfsv4_auth",  # this is None only in the default case
                           # when `nfsv4_support` is set to disabled
            }
    assert field.name == export.fields.get(field.name).name
    field_value = export.get_field(field.name)
    if field.name in fields_with_initial_none:
        assert field_value is None
    else:
        assert field_value is not None

def test_create_export_with_filesystem_name(infinibox, filesystem):
    export = create_export(infinibox, filesystem=filesystem.get_name())
    assert export.get_filesystem() == filesystem

def test_create_export_with_nfsv4(infinibox, filesystem):
    infinibox.update_nfs_server_capabilities(nfsv4_support="enabled")
    export = filesystem.add_export(nfs_version="nfsv4")
    assert export.get_nfs_version() == "NFSv4"
    assert export.get_nfsv4_auth() == ["SYS"]

def test_create_export_with_nfsv3(filesystem):
    export = filesystem.add_export()
    assert export.get_nfs_version() == "NFSv3"
    assert export.get_nfsv4_auth() is None

def test_create_export_with_nfsv4_without_enabling_it(filesystem):
    with pytest.raises(APICommandFailed) as exception:
        filesystem.add_export(nfs_version="nfsv4")
    assert exception.value.status_code == 409 
    assert exception.value.message == "The protocol version NFSV4 specified does not match the system settings"
