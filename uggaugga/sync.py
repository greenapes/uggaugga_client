#!/usr/bin/env python3
import client
import json
import sys

conf = None
with open('./uggaugga_config.json', 'r') as fp:
    conf = json.load(fp)

if not conf:
    raise Exception("file ./uggaugga_config.json not found")


DRY_RUN = False
if '--n' in sys.argv:
    DRY_RUN = True

extractors = []
for extr in conf['extractors']:
    
    if extr['type'] == 'TExtractor':
        extractors.append(client.TExtractor(
            root=extr['root'], 
            exts=extr['extention_list']),
            custom_regex=extr.get("custom_regex"))
        
    elif extr['type'] == 'XgettexExtractor':
        extractors.append(client.XgettexExtractor(
            root=extr['root'],
            ext=extr['extension'],
            language=extr['language'], 
            I18n_parent_key=extr['I18n_parent_key']))


client.config(namespace=conf['namespace'],
              connection_url=conf['server']['url'],
              public_key=conf['server']['public_key'],
              secret_key=conf['server']['secret_key'],
              supported_langs=conf['langs'],
              i18n_local_path=conf["i18n_path"],
              code_extractors=extractors)

I18N = client.sync(extract_from_code=True,
                   dry_run=DRY_RUN or conf.get('debug', False))
