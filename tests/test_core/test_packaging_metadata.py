from infinisdk.core.utils import packaging_metadata as pm


def test_get_distribution_version_known_package():
    # infinisdk is installed in the test env, so this resolves to a real version
    assert pm.get_distribution_version("infinisdk") != "N/A"


def test_get_distribution_version_missing_returns_na():
    assert pm.get_distribution_version("no-such-distribution-xyz") == "N/A"


def test_iter_entry_points_yields_entry_points_not_strings():
    # console_scripts exists in any real env. The bug was this yielding
    # group-name strings on 3.10/3.11 instead of EntryPoint objects.
    eps = list(pm.iter_entry_points("console_scripts"))
    assert all(hasattr(ep, "load") and hasattr(ep, "name") for ep in eps)


def test_iter_entry_points_unknown_group_is_empty():
    assert list(pm.iter_entry_points("infinisdk.cli.no_such_group")) == []
