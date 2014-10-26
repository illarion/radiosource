__author__ = 'shaman'


def parse_fn(fn):

    fn = fn.split('/')[-1]
    fn = fn.replace('_', ' ')
    fn = '.'.join(fn.split('.')[:-1])
    if '-' not in fn:
        return '', fn.strip()

    fn = fn.split('-', 1)
    return tuple([part.strip() for part in fn])
