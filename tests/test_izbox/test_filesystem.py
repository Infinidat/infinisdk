from capacity import GB

import pytest


def test_filesystem_get_set_quota(izbox, filesystem):
    assert filesystem.get_quota() == GB
    filesystem.update_quota(3 * GB)


def test_filesystem_name_autogeneration(izbox, filesystem):
    new_fs = izbox.filesystems.create()
    assert new_fs.get_name()


def test_create_filesystem_with_quota_direct(izbox, filesystem):
    fs = izbox.filesystems.create(name="bla", quota_in_bytes=1000000000)
    assert fs.get_quota() == GB


def test_filesystem_get_set_name(izbox, filesystem, fs_name):
    assert filesystem.get_name() == fs_name
    filesystem.update_name("new_name")


def test_create_snapshot(izbox, filesystem):
    snapshot = filesystem.create_snapshot("snap1")
    _check_snapshot(filesystem, snapshot)


def test_create_snapshot_directly(izbox, filesystem):
    snapshot = izbox.snapshots.create(filesystem_id=filesystem.id)
    _check_snapshot(filesystem, snapshot)


def _check_snapshot(filesystem, snapshot):
    assert snapshot in snapshot.system.objects.snapshots.find()
    assert snapshot.id != filesystem.id
    assert snapshot.get_parent() == filesystem
    assert snapshot in filesystem.get_snapshots()


def test_rollback(izbox, filesystem):
    snapshot = filesystem.create_snapshot()
    filesystem.rollback(snapshot)


def test_get_mount_path(izbox, filesystem):
    path = filesystem.get_mount_path()
    assert filesystem.get_name() in path

@pytest.fixture
def fs_name():
    return "fs_name"

@pytest.fixture
def filesystem(izbox, fs_name):
    return izbox.filesystems.create(name=fs_name)
