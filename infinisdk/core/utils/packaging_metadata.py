try:
    from importlib.metadata import PackageNotFoundError, entry_points, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, entry_points, version


def get_distribution_version(package_name):
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "N/A"


def iter_entry_points(group):
    eps = entry_points()
    if hasattr(eps, "select"):
        return eps.select(group=group)
    return eps.get(group, [])
