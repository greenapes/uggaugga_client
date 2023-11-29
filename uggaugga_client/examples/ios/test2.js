
i18n = {
    t: (x, obj) => {return x}
}

function T(key, _default) {
    const string = i18n.t(key);
    return (!string || string === key) ? _default : string;
}

function F(string, object) {
    const re = /{(.+?)}/gi;
    let res = string;
    let regex = re.exec(string);
    while (regex && regex[1]) {
      const ar = regex[1].split('.');
      let obj = object;
      ar.forEach((key) => {
        obj = obj[key];
      });
      obj = obj || '';
      res = res.replace(regex[0], obj);
      regex = re.exec(string);
    }
    return res.replace(/ +/g, ' ');
}

// flat
T("flat text")

// key nested
T("login.default", "hello!")

// format flat
F(T("login.custom"), {name: "amin"});

// format nested
F(T("login.custom", "hello {name}"), {name: "amin"});

// plurals NOT SUPPORTED
// way to
if(count > 1) {
    T("login.post.other", "here some posts")
}else {
    T("login.post.one", "here a post")
}

//array NOT SUPPORTED
// way to
const array = [
    T("login.avatars_0", "Mingo"),
    T("login.avatars_1", "Dugo"),
    T("login.avatars_2", "Minga"),
    T("login.avatars_3", "Gina"),
    T("login.avatars_4", "Ponce")
]

// DONT DO THIS (AUTO EXTRACTOR WILL NOT WORK)
var var1 = "myekey"
T(var1, 'pippo')