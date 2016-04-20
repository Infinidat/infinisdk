import os

from mitba import cached_function


@cached_function
def get_logged_in_username():
    try:
        import pwd
        user_id = os.getuid()
        os_info = pwd.getpwuid(user_id)
        return os_info.pw_name
    except ImportError:
        # For windows users
        return os.environ.get('USERNAME') or os.environ.get('USER', 'unknown')

@cached_function
def get_hostname():
    import socket
    return socket.getfqdn()
