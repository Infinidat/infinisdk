import pytest


@pytest.mark.parametrize("version_strings", [
    ("2.2.0.12", "2.2.0.2"),
    ("2.2.0.2-a", "2.2.0.2"),
    ("2.2.0.2-b", "2.2.0.2-a"),
    ("2.2.0.12-bla", "2.2.0.2"),
    ("2.2.0.22-dev", "2.2.0.12"),
    ("2.2.0.22-dev", "2.2.0.21"),
    ("2.2.0.22", "2.2.0.22-dev"),
    ])
def test_comparing_different_versions(infinibox, version_strings):
    gt_version_str, l_version_str = version_strings
    gt_version = infinibox.compat.normalize_version_string(gt_version_str)
    lt_version = infinibox.compat.normalize_version_string(l_version_str)
    assert gt_version != lt_version
    assert gt_version > lt_version
    assert lt_version < gt_version

@pytest.mark.parametrize('versions', [
    ("2.2.0.22-dev", "2.2.0.22-dev1"),
    ("2.2.0.22-dev", "2.2.0.22-dev"),
    ("2.2.0.22-dev", "2.2.0.22-dev-a"),
    ("2.2.0.22-dev", "2.2.0.22-weird"),
    ("2.2.0.22-weird", "2.2.0.22-dev"),
    ("2.2.0.22-dev-weird", "2.2.0.22-dev-weird"),
    ("2.2.0.22-weird", "2.2.0.22-weird"),
])
def test_comparing_non_comparable_versions(infinibox, versions):
    version_a, version_b = [infinibox.compat.normalize_version_string(x) for x in versions]
    assert version_a != version_b
    assert not (version_a == version_b)

def test_comparing_equal_versions(infinibox):
    version1 = infinibox.compat.normalize_version_string("2.2.0.2")
    version2 = infinibox.compat.normalize_version_string("2.2.0.2")
    assert version1 == version2
    assert not (version1 != version2)
    assert version1 >= version2
    assert version1 <= version2


@pytest.mark.parametrize("info_tuple", [
    ("2.2.0.23", (2,2,0,23,'*'), False, False),
    ("2.2.0.23-a", (2,2,0,23,'a'), False, False),
    ("2.2.0.23-dev", (2,2,0,23,'*'), True, False),
    ("2.2.0.23-dev2", (2,2,0,23,'*'), True, False),
    ("2.2.0.23-bla", (2,2,0,23,'*'), False, True),
    ])
def test_version_attributes(infinibox, info_tuple):
    version_str, expected_version, expected_is_dev, expected_is_odd_version = info_tuple
    version = infinibox.compat.normalize_version_string(version_str)
    assert version.version == expected_version
    assert version._is_dev == expected_is_dev
    assert version._is_odd_version == expected_is_odd_version
