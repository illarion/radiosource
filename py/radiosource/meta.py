__author__ = 'shaman'


def parse_fn(fn):
    """
    >>> parse_fn('/files/path/Omni Trio - Renegate Snares.ogg')
    'Omni Trio - Renegate Snares'
    >>> parse_fn('/files/path/Renegate Snares by Omni Trio.ogg')
    'Renegate Snares by Omni Trio'
    """
    fn = fn.split('/')[-1]  # remove all previous path
    fn = fn.replace('_', ' ')  # remove underscores
    fn = '.'.join(fn.split('.')[:-1])  # remove extension
    return fn.strip()
