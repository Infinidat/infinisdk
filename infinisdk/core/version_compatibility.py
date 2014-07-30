
class All(object):

    def __init__(self, major, minor):
        super(All, self).__init__()
        self.major = major
        self.minor = minor

    def matches(self, version_string):
        parts = version_string.split('.')
        try:
            major = int(parts[0])
            minor = int(parts[1])
        except (ValueError, IndexError):
            return False

        return (self.major, self.minor) <= (major, minor)
