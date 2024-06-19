import requests
import base64
import os
import ujson
from pprint import pprint
import re
import hashlib


ORIGINAL_LANGUAGE = 'ORIGINAL'
# example ['en', 'it']
SUPPORTED_LANGS = None  
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


def sync(extract_from_code=False, dry_run=False, import_data=None):
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

    if import_data:
        I18N = _merge(import_data, I18N)

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
        if DEFAULT_LANG:
            I18N[DEFAULT_LANG] = I18N[ORIGINAL_LANGUAGE]
            del I18N[ORIGINAL_LANGUAGE]

        if not DISABLE_UPLOAD:
            _upload(I18N)
        _save_to_file(I18N)

    return I18N


def clear_text(text):
    return text #.replace("\'", "'").replace('\\n', '\n')

class _Extractor():
    
    def extract():
        raise NotImplementedError()
    
    def _ios(self, path):
        import codecs
        encoded_text = open(path, 'rb').read()     #you should read in binary mode to get the BOM correctly
        bom = codecs.BOM_UTF16_LE                               #print dir(codecs) for other encodings
        assert encoded_text.startswith(bom)                     #make sure the encoding is what you expect, otherwise you'll get wrong data
        encoded_text = encoded_text[len(bom):]                  #strip away the BOM
        decoded_text = encoded_text.decode('utf-16le')
        return decoded_text


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
        if EXPORT_FORMAT == EXPORT_FORMAT_IOS:
            text = self._ios(path)
        else:
            with open(path, 'r') as f:
                text = f.read()

        return [clear_text(x) for x in re.findall(match, text)]

    def extract(self):
        print("Using TExtractor...")

        matches = []
        """
            [
                ('main.key_sample.sub', 'default value'), 
                (...)
            ]
        """
        if os.path.isfile(self.root):
            matches.extend(self._rewrite_code(self.root))
        else:
            for root, dirs, files in os.walk(self.root):
                for path in files:
                    matches.extend(self._rewrite_code(
                        os.path.join(root, path)))

        return matches_to_nested_i18n(matches)


class TExtractorFlat(_Extractor):

    def __init__(self, root, exts, text_key=False, I18n_parent_key=None, custom_regex=None) -> None:
        self.root = root
        self.text_key = text_key
        self.exts = [x.strip() if x[1] ==
                     '.' else f".{x.strip()}" for x in exts]
        self.I18n_parent_key = I18n_parent_key
        self.custom_regex = custom_regex
        if self.I18n_parent_key and self.text_key:
            raise Exception(
                "if text_as_key is disabled you cant set I18n_parent_key")

    def _rewrite_code(self, path):
        ext = os.path.splitext(path)[1]
        if ext not in self.exts:
            return []

        print(f"DEBUG: rewrite_code for {path}")

        match = r"""[{\s]*T\(['"](.*?)['"]\)(?s:.)"""

        if self.custom_regex:
            match = self.custom_regex
        if EXPORT_FORMAT == EXPORT_FORMAT_IOS:
            text = self._ios(path)
        else:
            with open(path) as f:
                text = f.read()
        return [clear_text(x) for x in re.findall(match, text)]

    def extract(self):
        print("Using TExtractorFlat...")

        matches = []
        """
            ["default value"]
        """
        if os.path.isfile(self.root):
            matches.extend(self._rewrite_code(self.root))
        else:
            for root, dirs, files in os.walk(self.root):
                for path in files:
                    matches.extend(self._rewrite_code(
                        os.path.join(root, path)))

        return matches_to_flat_i18n(matches, self.I18n_parent_key, self.text_key)


class XgettexExtractor(_Extractor):

    def __init__(self, root, ext, language, text_key=False, I18n_parent_key=None):
        self.root = root
        self.ext = ext
        self.language = language
        self.I18n_parent_key = I18n_parent_key
        self.text_key = text_key
        if self.I18n_parent_key and self.text_key:
            raise Exception(
                "if text_as_key is disabled you cant set I18n_parent_key")

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
                        t = "".join(buffer)
                        if t:
                            matches.append(t)
                        buffer = []
                    else:
                        t = line[1:-2]
                        buffer.append(t)
        os.remove(po_path)
        return matches_to_flat_i18n(matches, self.I18n_parent_key, self.text_key)


def matches_to_flat_i18n(matches, I18n_parent_key, text_key):
    """
    returns md5:value or value:value under each languages
        
    {
        'ORIGINAL': {
            'asnc1h89hj1ddjasdsad': "default value"
        }, 
        'it': {
            'asnc1h89hj1ddjasdsad': ""
        },
        ...
    }
    """
    print("parent ", I18n_parent_key)
    out = {}
    for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
        if I18n_parent_key:
            out[lang] = {I18n_parent_key: {}}
        else:
            out[lang] = {}
    for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
        for x in matches:
            if text_key:
                k = x
                v = x
            else:
                if type(x) == tuple:
                    k = hashlib.md5(x[0].encode()).hexdigest()
                    v = x[1]
                else:
                    k = hashlib.md5(x.encode()).hexdigest()
                    v = x
            
            dest = out[lang]
            if I18n_parent_key:
                dest = out[lang][I18n_parent_key]
            dest[k] = v if lang == ORIGINAL_LANGUAGE else ''
    return out
        
def matches_to_nested_i18n(matches):
    out = {}
    """ 
    returns nested key.sub:value under each languages
    
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
        for x in matches:
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


def import_po(po_path, lang, dry_run=False):
    i18n_imported = _extract_from_po(po_path)
    data = {lang: i18n_imported}
    sync(extract_from_code=True, dry_run=dry_run, import_data=data)

       
# === PRIVATE METHODS ===

def _extract_from_po(po_path):
    matches = {}
    with open(po_path, 'r') as fp:
        buffer = []
        buffer_msg = []
        current_key = None
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
                        k = hashlib.md5(t.encode()).hexdigest()
                        current_key = k
                        buffer_msg.append(line.split("msgstr \"", 1)[1][:-2])
                    buffer = []
                else:
                    t = line[1:-2]
                    buffer.append(t)
            elif current_key:
                if line.strip() == "":
                    buffer_msg = [x for x in buffer_msg if x]
                    v = "\n".join(buffer_msg)
                    matches[current_key] = v
                    buffer_msg = []
                    current_key = None
                else:
                    t = line[1:-2]
                    buffer_msg.append(t)
    return matches

def _save_json(i18n_data):
    with open(I18N_LOCAL_PATH, 'w+') as fp:
        ujson.dump(i18n_data, fp, indent=2, escape_forward_slashes=True)


def _save_android(i18n_data):
    for lang in i18n_data.keys():
        if lang == DEFAULT_LANG:
            folder = "values"
        else:
            folder = f"values-{lang}"
        os.makedirs(os.path.join(I18N_LOCAL_PATH, folder), exist_ok=True)

        path = 'strings.xml'
        old_file = ""
        with open(os.path.join(I18N_LOCAL_PATH, folder, path), 'r+') as fp:
            pattern = r"<string\s.*?</string>\n"
            pattern_header1 = r"<\?xml\s.*?\?>"
            pattern_header2 = r"<resources\s.*?\">"
            pattern_footer = r"</resources>"
            pattern_comment = r"<\!--.*?-->"
            old_file = re.sub(pattern, '', fp.read())
            old_file = re.sub(pattern_header1, '', old_file)
            old_file = re.sub(pattern_header2, '', old_file)
            old_file = re.sub(pattern_footer, '', old_file)
            old_file = re.sub(pattern_comment, '', old_file)
       
        xml_header = """<?xml version="1.0" encoding="utf-8"?>
    <resources xmlns:tools="http://schemas.android.com/tools" tools:ignore="MissingTranslation, TypographyEllipsis, Typos">
"""
        xml_footer = """
</resources>
"""
       
        with open(os.path.join(I18N_LOCAL_PATH, folder, path), 'w+') as fp:
            fp.write(xml_header)
            data = _flatten_data(i18n_data[lang], sep="_")
            for k in data.keys():
                fp.write(f'<string name="{k}">{data[k]}</string>' + '\n')
            fp.write(old_file)
            fp.write(xml_footer)


def _save_ios(i18n_data):
    for lang in i18n_data.keys():
        path = f'Localizable.strings'
        if lang == DEFAULT_LANG:
            folder = "Base.lproj"
        else:
            folder = f"{lang}.lproj"
        os.makedirs(os.path.join(I18N_LOCAL_PATH, folder), exist_ok=True)
        
        with open(os.path.join(I18N_LOCAL_PATH, folder, path), 'wb+') as fp:
            data = _flatten_data(i18n_data[lang], sep=".")
            import codecs
            fp.write(codecs.BOM_UTF16_LE)
            for k in data.keys():
                key = i18n_data[DEFAULT_LANG][k] # CODICE ORRENDO
                key = key.replace('%1$@', '%@') # CODICE ORRENDO 
                key = key.replace('%2$@', '%@') # CODICE ORRENDO
                key = key.replace('%3$@', '%@') # CODICE ORRENDO
                key = key.replace('%4$@', '%@') # CODICE ORRENDO
                key = key.replace('%1$d', '%d') # CODICE ORRENDO
                key = key.replace('%2$d', '%d') # CODICE ORRENDO
                key = key.replace('%3$d', '%d') # CODICE ORRENDO
                key = key.replace('%4$d', '%d') # CODICE ORRENDO

                value = data[k].replace('"', '\"') 
                fp.write("/* No comment provided by engineer. */\n".encode("utf-16le"))
                fp.write((f'"{key}" = "{value}";' + '\n').encode("utf-16le"))
                fp.write("\n".encode("utf-16le"))


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
                         json={'i18n': data, 'namespace': NAMESPACE, 'default_lang': DEFAULT_LANG})
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


def _flatten_data(y, sep='.'):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + sep)
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + sep)
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out
