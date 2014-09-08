import pytest
from infinisdk.core.exceptions import APICommandFailed

from infinisdk.infinibox.filesystem import Filesystem
from infinisdk.infinibox.pool import Pool


def test_exporting(infinibox, filesystem):
    assert not filesystem.get_exports()
    export = filesystem.add_export()
    assert filesystem.get_exports()[0] == export
    assert len(filesystem.get_exports()) == 1
    assert export in infinibox.exports.get_all()
    export.delete()
    assert not filesystem.get_exports()
    assert export not in infinibox.exports.get_all()


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


def test_filesystem_children_deletion(filesystem):
    snap = filesystem.create_snapshot()
    clone = snap.create_clone()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    with pytest.raises(APICommandFailed) as caught:
        snap.delete()
    clone.delete()
    with pytest.raises(APICommandFailed) as caught:
        filesystem.delete()
    snap.delete()
    filesystem.delete()


def test_field_types():
    assert Filesystem.fields.parent.type.type is Filesystem
    assert Filesystem.fields.pool.type.type is Pool


def test_restore(infinibox, filesystem):
    snapshot = filesystem.create_snapshot()

    assert filesystem.is_master()
    assert snapshot.is_snapshot()

    with pytest.raises(NotImplementedError) as caught:
        filesystem.restore(snapshot)

    snapshot.delete()
    assert (not snapshot.is_in_system())
