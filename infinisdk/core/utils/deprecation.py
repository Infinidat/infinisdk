import vintage

# Backward compatibility for deprecation utils
# Need to be deleted after next (customer) version
# No longer exist: forget_deprecation_locations

def deprecated(func=None, message=None):
    vintage.warn_deprecation('Use vintage.deprecated instead', frame_correction=1)
    return vintage.deprecated(func=func, message=message)

def get_no_deprecations_context():
    vintage.warn_deprecation('Use vintage.get_no_deprecations_context instead', frame_correction=1)
    return vintage.get_no_deprecations_context()
