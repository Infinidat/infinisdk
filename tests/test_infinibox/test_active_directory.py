from munch import Munch


def test_active_directory_set_unix_services_disabled(
    infinibox_with_network_space, active_directory_with_unix_services_enabled
):  # pylint: disable=unused-argument
    assert active_directory_with_unix_services_enabled.unix_services_enabled == True
    assert active_directory_with_unix_services_enabled.uid_attribute_name == "uidNumber"
    assert active_directory_with_unix_services_enabled.gid_attribute_name == "gidNumber"

    active_directory_unix_services_disabled = Munch(
        infinibox_with_network_space.active_directory_domains.set_unix_services(
            unix_services_enabled=False
        )
    )

    assert active_directory_unix_services_disabled.unix_services_enabled == False
    assert active_directory_unix_services_disabled.uid_attribute_name == None
    assert active_directory_unix_services_disabled.gid_attribute_name == None


def test_active_directory_set_max_translated_groups(
    infinibox_with_network_space, active_directory_with_unix_services_enabled
):  # pylint: disable=unused-argument
    active_directory = Munch(
        infinibox_with_network_space.active_directory_domains.set_max_translated_groups(
            max_translated_groups=20
        )
    )

    assert active_directory.max_translated_groups == 20
