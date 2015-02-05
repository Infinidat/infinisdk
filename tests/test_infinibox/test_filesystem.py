import pytest

from infinisdk._compat import httplib
from infinisdk.core.exceptions import APICommandFailed
from infinisdk.infinibox.filesystem import Filesystem
from infinisdk.infinibox.pool import Pool

from ..conftest import new_to_version


@new_to_version('2.0')
def test_exporting(infinibox, filesystem):
    assert not filesystem.get_exports()
    export = filesystem.add_export()
    assert filesystem.get_exports()[0] == export
    assert len(filesystem.get_exports()) == 1
    assert export in infinibox.exports.get_all()
    export.delete()
    assert not filesystem.get_exports()
    assert export not in infinibox.exports.get_all()


@new_to_version('2.0')
def test_export_deletion(filesystem):
    filesystem.add_export()
    filesystem.add_export()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    filesystem.get_exports()[0].delete()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    filesystem.get_exports()[0].delete()
    filesystem.delete()


@new_to_version('2.0')
def test_filesystem_children_deletion_without_approval(filesystem):
    snap = filesystem.create_snapshot()
    clone = snap.create_clone()
    with filesystem.system.api.get_unapproved_context():
        with pytest.raises(APICommandFailed) as caught:
            filesystem.delete()
    assert caught.value.status_code == httplib.FORBIDDEN

    filesystem.delete()
    assert not filesystem.is_in_system()
    assert not snap.is_in_system()
    assert not clone.is_in_system()


@new_to_version('2.0')
def test_field_types():
    assert Filesystem.fields.parent.type.type is Filesystem
    assert Filesystem.fields.pool.type.type is Pool
