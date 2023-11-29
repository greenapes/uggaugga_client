import requests
import base64
import os
import json
from pprint import pprint
import re
import hashlib


ORIGINAL_LANGUAGE = 'ORIGINAL'
SUPPORTED_LANGS = None  # example ['en', 'it']
I18N_LOCAL_PATH = None
extractors = None
NAMESPACE = None
EXPORT_FORMAT_JSON = 'json'
EXPORT_FORMAT_ANDROID = 'xml_android'
EXPORT_FORMAT_IOS = 'strings_ios'
EXPORT_FORMAT = EXPORT_FORMAT_JSON
DISABLE_UPLOAD = False
DEFAULT_LANG = None

base = None
token = None


def config(namespace: str,
           connection_url: str,
           public_key: str,
           secret_key: str,
           supported_langs: list,
           i18n_local_path: str,
           disable_upload=False,
           default_lang=None,
           code_extractors=None,
           export_format=EXPORT_FORMAT_JSON) -> None:
    """
    ### params
    - namespace: is the i18n namaspace for this project
    - connection_url: is your uggaugga server instance base_url
    - public_key: is your uggaugga server instance public_key
    - secret_key: is your uggaugga server instance secret_key (keep it secret!)
    - supported_langs: is the list of supported lang, each lang is 2 letter locale 
                       format, example: 'en', 'it','de','jp'...
    - code_extractors: the list of code extractor used to extract strings from code.
                       must be on of available extractors: TExtractor or XgettexExtractor
    """
    global base, token, I18N_LOCAL_PATH, SUPPORTED_LANGS, extractors, NAMESPACE, EXPORT_FORMAT, DISABLE_UPLOAD, DEFAULT_LANG
    NAMESPACE = namespace
    base = connection_url
    token = base64.b64encode(f"{public_key}:{secret_key}".encode())
    SUPPORTED_LANGS = supported_langs
    I18N_LOCAL_PATH = i18n_local_path
    DISABLE_UPLOAD = disable_upload
    extractors = code_extractors
    EXPORT_FORMAT = export_format
    DEFAULT_LANG = default_lang


def sync(extract_from_code=False, dry_run=False):
    assert I18N_LOCAL_PATH
    assert base
    assert token
    assert SUPPORTED_LANGS
    assert extractors
    assert NAMESPACE

    I18N = {}

    if extract_from_code:
        for extractor in extractors:
            extractor: _Extractor
            from_code_i18n = extractor.extract()
            I18N = _merge(from_code_i18n, I18N)
            print(
                f"[MERGED] with from_code_i18n -> I18N = I18N USING {extractor.__class__.__name__}")

    remote_i18n = _download()

    if remote_i18n:
        for lang in SUPPORTED_LANGS:
            I18N[lang] = _find_and_place(
                place_in=I18N[lang], search_in=remote_i18n[lang])

    if dry_run:
        print("DRY RUN MODE")
        print(f"namespace = {NAMESPACE}")
        pprint(I18N, indent=2)
    else:
        if not DISABLE_UPLOAD:
            _upload(I18N)
        _save_to_file(I18N)

    return I18N


class _Extractor():

    def extract():
        raise NotImplementedError()


class TExtractor(_Extractor):

    def __init__(self, root, exts, custom_regex=None) -> None:
        self.root = root
        self.exts = [x.strip() if x[1] ==
                     '.' else f".{x.strip()}" for x in exts]
        self.custom_regex = custom_regex

    def _rewrite_code(self, path):
        ext = os.path.splitext(path)[1]
        if ext not in self.exts:
            return []

        print(f"DEBUG: rewrite_code for {path}")

        match = r"""[{\s]*T\(['"](.*?)['"]\s*,\s*['"](.*?)['"]\)(?s:.)"""

        if self.custom_regex:
            match = self.custom_regex
        with open(path) as f:
            text = f.read()
            return re.findall(match, text)

    def extract(self):
        print("Using TExtractor...")

        out_text = []
        """
            [
                ('main.key_sample.sub', 'default value'), 
                (...)
            ]
        """
        if os.path.isfile(self.root):
            out_text.extend(self._rewrite_code(self.root))
        else:
            for root, dirs, files in os.walk(self.root):
                for path in files:
                    out_text.extend(self._rewrite_code(
                        os.path.join(root, path)))

        out = {}
        """ 
        {
            'ORIGINAL': {
                'main': {
                    'key_sample': {
                        'sub': 'default value'
                    } 
                }
            }, 
            'it': {
                'main': {
                    'key_sample': {
                        'sub': '',
                    }
                }
            },
            ...
        }
        """
        for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
            out[lang] = {}
        for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
            for x in out_text:
                key_flatten, default = x
                tmp = None
                subs = key_flatten.split('.')
                out_lang = out[lang]
                for index, sub in enumerate(subs):
                    if tmp is None:
                        if not out_lang.get(sub):
                            last_iter = len(subs) - 1 == index
                            value = default if lang == ORIGINAL_LANGUAGE else ''
                            out_lang[sub] = value if last_iter else {}
                        tmp = out_lang[sub]
                    else:
                        if not tmp.get(sub):
                            tmp[sub] = {}
                        if len(subs) - 1 == index:
                            tmp[sub] = default if lang == ORIGINAL_LANGUAGE else ''
                        else:
                            tmp = tmp[sub]
        return out


class TExtractorFlat(_Extractor):

    def __init__(self, root, exts, text_key=False, I18n_parent_key=None, custom_regex=None) -> None:
        self.root = root
        self.text_key = text_key
        self.exts = [x.strip() if x[1] ==
                     '.' else f".{x.strip()}" for x in exts]
        if self.I18n_parent_key and self.text_key:
            raise Exception(
                "if text_as_key is disabled you cant set I18n_parent_key")
        self.I18n_parent_key = I18n_parent_key
        self.custom_regex = custom_regex

    def _rewrite_code(self, path):
        ext = os.path.splitext(path)[1]
        if ext not in self.exts:
            return []

        print(f"DEBUG: rewrite_code for {path}")

        match = r"""[{\s]*T\(['"](.*?)['"]\)(?s:.)"""

        if self.custom_regex:
            match = self.custom_regex
        with open(path) as f:
            text = f.read()
            return re.findall(match, text)

    def extract(self):
        print("Using TExtractorFlat...")

        out_text = []
        """
            ["default value"]
        """
        if os.path.isfile(self.root):
            out_text.extend(self._rewrite_code(self.root))
        else:
            for root, dirs, files in os.walk(self.root):
                for path in files:
                    out_text.extend(self._rewrite_code(
                        os.path.join(root, path)))

        out = {}
        """ 
        {
            'ORIGINAL': {
                'asdasdasdasd': "default value"
            }, 
            'it': {
                'asdasdasdasd': ""
            },
            ...
        }
        """
        out = {}
        for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
            if self.text_key:
                out[lang] = {}
            else:
                out[lang] = {self.I18n_parent_key: {}}
        for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
            for x in out_text:
                if self.text_key:
                    out[lang][x] = x if lang == ORIGINAL_LANGUAGE else ''
                else:
                    k = hashlib.md5(x.encode()).hexdigest()
                    out[lang][self.I18n_parent_key][k] = x if lang == ORIGINAL_LANGUAGE else ''
        return out


class XgettexExtractor(_Extractor):

    ext = None
    language = None
    root = '.'
    I18n_parent_key = 'strings'

    def __init__(self, root, ext, language, I18n_parent_key):
        self.root = root
        self.ext = ext
        self.language = language
        self.I18n_parent_key = I18n_parent_key

    def extract(self):
        print("Using XgettexExtractor...")
        po_path = "./tmp.po"
        os.system(
            f'find {self.root} -name \*.{self.ext} | xgettext -o {po_path} --from-code=UTF-8 -L {self.language} -f -')

        matches = []
        with open(po_path, 'r') as fp:
            buffer = []
            for line in fp.readlines():
                if line.startswith("msgid \""):
                    t = line.split("msgid \"", 1)[1]
                    if len(t) >= 2:
                        buffer.append(t[:-2])
                elif buffer:
                    if line.startswith('msgstr "'):
                        buffer = [x for x in buffer if x]
                        t = "\n".join(buffer)
                        if t:
                            matches.append(t)
                        buffer = []
                    else:
                        t = line[1:-2]
                        buffer.append(t)
        os.remove(po_path)
        out = {}
        for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
            out[lang] = {self.I18n_parent_key: {}}
        for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
            for x in matches:
                k = hashlib.md5(x.encode()).hexdigest()
                out[lang][self.I18n_parent_key][k] = x if lang == ORIGINAL_LANGUAGE else ''
        return out


# === PRIVATE METHODS ===

def _save_json(i18n_data):
    with open(I18N_LOCAL_PATH, 'w+') as fp:
        json.dump(i18n_data, fp, indent=2)


def _save_android(i18n_data):
    for lang in i18n_data.keys():
        path = f'values{"" if lang == (DEFAULT_LANG or "en") else f"-{lang}"}.xml'
        with open(os.path.join(I18N_LOCAL_PATH, path), 'a+') as fp:
            if DEFAULT_LANG and lang == ORIGINAL_LANGUAGE:
                continue
            if DEFAULT_LANG and lang == DEFAULT_LANG:
                data = _flatten_data(i18n_data[ORIGINAL_LANGUAGE])
            else:
                data = _flatten_data(i18n_data[lang])
            for k in data.keys():
                fp.write(f'<string name="{k}">{data[k]}</string>' + '\n')


def _save_ios(i18n_data):
    for lang in i18n_data.keys():
        path = f'values{"" if lang == "en" else f"-{lang}"}.xml'
        with open(os.path.join(I18N_LOCAL_PATH, path), 'a+') as fp:
            if DEFAULT_LANG and lang == ORIGINAL_LANGUAGE:
                continue
            if DEFAULT_LANG and lang == DEFAULT_LANG:
                data = _flatten_data(i18n_data[ORIGINAL_LANGUAGE])
            else:
                data = _flatten_data(i18n_data[lang])
            for k in data.keys():
                fp.write(f'"{k}" = "{data[k]}"' + '\n')


def _save_to_file(i18n_data):
    if EXPORT_FORMAT == EXPORT_FORMAT_JSON:
        _save_json(i18n_data)
    elif EXPORT_FORMAT == EXPORT_FORMAT_ANDROID:
        _save_android(i18n_data)
    elif EXPORT_FORMAT == EXPORT_FORMAT_IOS:
        _save_ios(i18n_data)

    print(f"File {I18N_LOCAL_PATH} saved")


def _download():
    try:
        resp = requests.get(f'{base}/api/{NAMESPACE}/download', headers={
            'Authorization': f'Basic {token.decode()}'
        })
        data = resp.json()
        if resp.status_code == 200:
            print("[LOADED] remote i18n")
        else:
            print("Error occurrend", resp.status_code, resp.text)
        return data
    except:
        print(
            f"[REMOTE NOT FOUND] not found I18N file for namespace={NAMESPACE}")
        return {}


def _upload(data):
    print(f"* Uploading roots strings to uggaugga namespace={NAMESPACE}")
    resp = requests.post(f'{base}/api/{NAMESPACE}/upload',
                         headers={
                             'Authorization': f'Basic {token.decode()}',
                             'Content-type': 'Application/json'},
                         json={'i18n': data, 'namespace': NAMESPACE})
    print(resp)
    return resp


def _merge(source, destination):
    """
    deep merge 2 dict, not replace is new val is empty

    nosetest 

    >>> a = { 'server' :            { 'strings' : { 'str_1' : 'val',     'str_2' : 'val2', 'str_3': '' } } }
    >>> b = { 'server' :            { 'strings' : { 'str_1' : 'replace', 'str_2' : '',     'str_3' : 'fill', 'str_4': 'add'} } }
    >>> merge(b, a) == { 'server' : { 'strings' : { 'str_1' : 'replace', 'str_2' : 'val2', 'str_3' : 'fill', 'str_4': 'add'} } }
    True
    """
    for key, new_value in source.items():
        if isinstance(new_value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            _merge(new_value, node)
        else:
            if new_value or not destination.get(key):
                # replace only if new_value is not empty string
                destination[key] = new_value

    return destination


def _find_and_place(place_in, search_in):
    for key, new_value in place_in.items():
        if search_in.get(key):
            if isinstance(new_value, dict):
                # get node or create one
                _find_and_place(place_in=new_value, search_in=search_in[key])
            else:
                place_in[key] = search_in[key]
    return place_in


def _flatten_data(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out
