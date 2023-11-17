import client

SUPPORTED_LANGS = ['it', 'en']
I18N_PATH = "./i18n.json"
DRY_RUN = False

url = 'http://127.0.0.1:5005'
public_key = 'uggaugga'
secret_key = 'd4ffa04d5a4f742e90525959301e43aa6bc2cd1e565a7400f0367bbb2b14a893'

extractors = [
    client.XgettexExtractor(root='./example_app/',
                            ext='py',
                            language='python', 
                            I18n_parent_key='strings')
]

client.config(namespace='roots',
              connection_url=url,
              public_key=public_key,
              secret_key=secret_key,
              supported_langs=SUPPORTED_LANGS,
              i18n_local_path=I18N_PATH,
              code_extractors=extractors)

I18N = client.sync(extract_from_code=True,
                   dry_run=False)
