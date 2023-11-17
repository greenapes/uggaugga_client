import requests
import base64
import os
import json
from pprint import pprint
import re


ORIGINAL_LANGUAGE = 'ORIGINAL'
SUPPORTED_LANGS = None  # example ['en', 'it']
I18N_LOCAL_PATH = None
extractors = None

base = None
token = None


def config(connection_url: str,
           public_key: str,
           secret_key: str,
           supported_langs: list,
           i18n_local_path: str,
           code_extractors=None) -> None:
    """
    ### params
    - connection_url: is your uggaugga server instance base_url
    - public_key: is your uggaugga server instance public_key
    - secret_key: is your uggaugga server instance secret_key (keep it secret!)
    - supported_langs: is the list of supported lang, each lang is 2 letter locale 
                       format, example: 'en', 'it','de','jp'...
    """
    global base, token, I18N_LOCAL_PATH, SUPPORTED_LANGS, extractors
    base = connection_url
    token = base64.b64encode(f"{public_key}:{secret_key}".encode())
    SUPPORTED_LANGS = supported_langs
    I18N_LOCAL_PATH = i18n_local_path
    extractors = code_extractors


def sync(extract_from_code=False, dry_run=False):
    assert I18N_LOCAL_PATH
    assert base
    assert token
    assert SUPPORTED_LANGS
    assert extractors
    local_i18n = {}
    try:
        with open(I18N_LOCAL_PATH, 'r') as fp:
            local_i18n = json.load(fp)
            print("[LOADED] local i18n file")
    except:
        raise Exception('local i18n not found')

    I18N = {}

    if extract_from_code:
        for extractor in extractors:
            extractor: _Extractor
            from_code_i18n = extractor.extract()

            I18N = _merge(from_code_i18n, I18N)
            print(f"[MERGED] with from_code_i18n -> I18N = I18N USING {extractor.__class__.__name__}")
    
    remote_i18n = _download()
    
    for lang in SUPPORTED_LANGS:
        I18N[lang] = _find_and_place(place_in=I18N[lang], search_in=remote_i18n[lang])

    if dry_run:
        print("DRY RUN MODE")
        pprint(I18N, indent=2)
    else:
        _upload(I18N)
        _save_to_file(I18N)

    return I18N



class _Extractor():
    
    def extract():
        raise NotImplementedError()
        
class TExtractor(_Extractor):
    
    def __init__(ext) -> None:
        ext = ext
    
    def _rewrite_code(self, path):
        if self.ext in ('.html'):
            mode = 'template'
        elif self.ext in ('.js', '.ts', '.jsx', '.tsx'):
            mode = 'js'

        if mode == 'template':
            match = r"""{{\s*T\s+['"](.*)['"]\s*}}"""
        else:
            match = r"""[{\s]\s*T\(['"](.*)['"]\)\s*}?"""
        replace = r""" "\1", """

        with open(path) as f:
            return re.sub(match, replace, f.read())
        
    def extract(self):
        print("Using TExtractor...")

        os.system("""
            find ./login -name '*.%s' -exec sh -c 'SRC=$1; DST=mirror_templates/$1;
            mkdir -p 'dirname ${DST}' && ./locales/rewrite_templates.py ${SRC} > ${DST}' _ {} \ """
            % self.ext)

        os.system("""
	        find mirror_templates/ -name "*.%s" | xgettext --files-from=- --output=tmp_locales/login.po --language=C
                  """ % self.ext)

class XgettexExtractor(_Extractor):
    
    ext = None
    language = None
    I18n_namespace = 'strings'
    
    def __init__(self, ext, language, I18n_namespace):
        ext = ext
        language = language
        I18n_namespace = I18n_namespace
    
    def extract(self):
        print("Using XgettexExtractor...")
        import hashlib
        po_path = "./tmp.po"
        
        os.system(
            f'find . -name \*.{self.ext} | xgettext -o {po_path} --from-code=UTF-8 -L {self.language} -f -')

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
            out[lang] = {self.I18n_namespace: {}}
        for lang in SUPPORTED_LANGS + [ORIGINAL_LANGUAGE]:
            for x in matches:
                k = hashlib.md5(x.encode()).hexdigest()
                out[lang][self.I18n_namespace][k] = x if lang == ORIGINAL_LANGUAGE else ''

        return out


# === PRIVATE METHODS ===


def _save_to_file(i18n_data):
    with open(I18N_LOCAL_PATH, 'w+') as fp:
        json.dump(i18n_data, fp, indent=2)
    print(f"File {I18N_LOCAL_PATH} saved")


def _download():
    resp = requests.get(f'{base}/api/i18n/download', headers={
        'Authorization': f'Basic {token.decode()}'
    })
    data = resp.json()
    if resp.status_code == 200:
        print("[LOADED] remote i18n")
    else:
        print("Error occurrend", resp.status_code, resp.text)
    return data


def _upload(data):
    print("* Uploading roots strings to uggaugga")
    resp = requests.post(f'{base}/api/i18n/upload',
                         headers={
                             'Authorization': f'Basic {token.decode()}',
                             'Content-type': 'Application/json'},
                         json={'i18n': data})
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
            if new_value:
                # replace only if new_value is not empty string
                destination[key] = new_value

    return destination

def _find_and_place(place_in, search_in):
    for key, new_value in place_in.items():
        if search_in.get(key):
            if isinstance(new_value, dict):
                # get node or create one
                search_in = search_in[key]
                place_in = new_value
                _find_and_place(place_in, search_in)
            else:
                place_in[key] = new_value
    return place_in