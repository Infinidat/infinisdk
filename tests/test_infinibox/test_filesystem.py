import http.client as httplib
import pytest

from infinisdk.core.exceptions import APICommandFailed
from infinisdk.infinibox.filesystem import Filesystem
from infinisdk.infinibox.pool import Pool


def test_filesystem_exporting(infinibox, filesystem):
    assert not filesystem.get_exports()
    export = filesystem.add_export()
    assert filesystem.get_exports()[0] == export
    assert len(filesystem.get_exports()) == 1
    assert export in infinibox.exports.get_all()
    export.delete()
    assert not filesystem.get_exports()
    assert export not in infinibox.exports.get_all()


def test_filesystem_with_exports_deletion(filesystem):
    filesystem.add_export()
    filesystem.add_export()
    with pytest.raises(APICommandFailed) as caught:  # pylint: disable=unused-variable
        filesystem.delete()
    filesystem.get_exports()[0].delete()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    filesystem.get_exports()[0].delete()
    filesystem.delete()


def test_filesystem_children_deletion_without_approval(filesystem):
    snap = filesystem.create_snapshot()
    clone = snap.create_snapshot()
    with filesystem.system.api.get_unapproved_context():
        with pytest.raises(APICommandFailed) as caught:
            filesystem.delete()
    assert caught.value.status_code == httplib.FORBIDDEN

    filesystem.delete()
    assert not filesystem.is_in_system()
    assert not snap.is_in_system()
    assert not clone.is_in_system()


def test_field_types():
    assert Filesystem.fields.parent.type.type is Filesystem  # pylint: disable=no-member
    assert Filesystem.fields.pool.type.type is Pool  # pylint: disable=no-member


def test_count_inside_fetch_once_context(filesystem):
    system = filesystem.system
    with system.filesystems.fetch_once_context():
        assert system.filesystems.count() == 1
