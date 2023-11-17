_ = lambda x: x

def foo():
    t = _('Hello')


def foo2():
    xx = 'asad' + _('Welcome here {name}!').format(name="Marco")