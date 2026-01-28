# pylint: disable=unused-argument
import pytest
from ..conftest import create_share
from infinisdk.infinibox.share import Share


def test_get_filesystem(infinibox, filesystem, share):
    assert share.get_filesystem() == filesystem

SKIPPED_FIELDS = {
    "internal_base_path",
    "user_dir_auto_create",
    "user_directory",
}

@pytest.mark.parametrize('field', Share.FIELDS)
def test_verify_fields(infinibox, share, field):
    if field.name in SKIPPED_FIELDS:
        pytest.skip("Skipping field '{}' due to field is only for home share".format(field.name))
    if not infinibox.compat.is_feature_supported(field.feature_name):
        pytest.skip('System does not support {}'.format(field.feature_name))
    assert field.name == share.fields.get(field.name).name
    assert share.get_field(field.name) is not None

def test_create_share_with_filesystem_name(infinibox, filesystem):
    share = create_share(infinibox, filesystem=filesystem.get_name())
    assert share.get_filesystem() == filesystem

def test_create_share_permissions(infinibox, filesystem_windows):
    smb_user = infinibox.smb_users.create(name="user1")
    share = create_share(infinibox, filesystem=filesystem_windows.get_name())
    # method not yet implemented
    share_permission = share.permissions.create(sid=smb_user.get_sid(), access="READONLY")
    assert share_permission.get_parent() == share

def test_home_shares(infinibox, filesystem_windows):
    home_share = infinibox.shares.create(
        filesystem=filesystem_windows,
        internal_base_path="/",
        home_share=True,
        user_dir_auto_create=True,
    )

    assert home_share.get_filesystem() == filesystem_windows
    assert home_share.get_user_directory() == "%d/%u"
    assert home_share.is_home_share() == True


def test_create_home_share_permissions(infinibox, filesystem_windows):
    smb_user = infinibox.smb_users.create(name="user1")
    home_share = infinibox.shares.create(
        filesystem=filesystem_windows,
        internal_base_path="/",
        home_share=True,
        user_dir_auto_create=True,
    )
    share_permission = home_share.permissions.create(
        sid=smb_user.get_sid(), access="READONLY"
    )

    assert share_permission.get_parent() == home_share
    assert share_permission.get_parent().get_name() == home_share.get_name()
    assert share_permission.get_access() == "READONLY"
