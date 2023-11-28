
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

// forat nested
F(T("login.custom", "hello {name}"), {name: "amin"});

// plurals
if(count > 1) {
    T("login.post.other", "here some posts")
}else {
    T("login.post.one", "here a post")
}

//array
/**
 * "login": {
 *    "avatars": [
 *      "Mingo",
 *       "Dugo"
 *    ]
 * }
 */
T("login.avatars", "unknown")[0]

// NON FARE MAI!
var var1 = "myekey"
T(var1, 'pippo')