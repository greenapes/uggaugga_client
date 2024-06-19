_ = lambda x: x

def foo():
    t = _('Hello')


def foo2():
    xx = 'asad' + _('Welcome here {name}!').format(name="Marco")
    
    messages = [
                _("""Hi
welcome to the Jungle!
I'm greenApes Community Manager if you have any question about greenApes or
need help in the Jungle, feel free to drop me a line here :).

See you in the Jungle, ook ook!"""),
            ]