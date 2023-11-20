T = () => {}

const foo = () => {
    t = T('main.hello', 'Hello');
}


function foo2() {
    xx = 'asad' + T('main.welcome_message', 'Welcome here {name}!').format(name="Marco")
    return xx
}

