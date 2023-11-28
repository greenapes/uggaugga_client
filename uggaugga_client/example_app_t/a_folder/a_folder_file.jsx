T = () => {}

const foo = () => {
    const var_ = "pippo";

    t = T('main.component.nested_1', 'i have earned something');
    t2 = T('main.component.nested_2', 'i have earned {twin}  for seaon {season_name}!').replace('{twin}', '10').repalce('{season_name}', 'winter');
    t3 = T('main.component.nested_3', "Chose: {twin} or {me}? ").replace('{twin}', 10).replace('{me}', 'marco')
    t4 = T('main.component.nested_4', 'hello {var}').repalce('{var}', var_)
}
