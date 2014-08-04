
class All(object):

    def __init__(self, major, minor):
        super(All, self).__init__()
        self.major = major
        self.minor = minor

    def matches(self, version_string):
        removed_labels = version_string.split("-")[0]
        parts = removed_labels.split('.')
        try:
            major = int(parts[0])
            minor = int(parts[1])
        except (ValueError, IndexError):
            return False

        return (self.major, self.minor) <= (major, minor)
