# api per i client

## installation

To get latest version run `pip install git+https://github.com/greenapes/uggaugga_client.git@master#egg=uggaugga --upgrade`

## project config
Under your project folder root create the file `uggaugga_config.json`

**Sample:**
```json
{
    "namespace": "sample_app",
    "langs": ["it", "en"],
    "i18n_path": "./locales/i18n.json",
    "server": {
        "url": <my uggaugga server url>,
        "public_key": <my uggaugga server public key>,
        "secret_key": <my uggaugga server secret key>
    },
    "extractors": [
        {
            "type": "XgettexExtractor",
            "note": "App with only strings, not key. Extract from `_('my text')`",
            "root": "./example_app_xgettext",
            "extension": "py",
            "language": "python",
            "I18n_parent_key": "server_strings"
        },
        {
            "type": "TExtractor",
            "note": "App with i18n key nested structure, extract from `T('key.nested', 'default text')` ",
            "root": "./example_app_t",
            "extention_list": ["js", "ts", "jsx", "tsx"]
        },
        {
            "type": "TExtractor",
            "note": "Custom extractor with i18n key nested. Extract from `{{ T 'key.nested' 'default text' }}`",
            "root": "./custom_app",
            "custom_regex": "{{\\s*T\\s+['\"](.*)['\"]\\s*['\"](.*?)['\"]\\s*}}",
            "extension_list": ["html"]
        },
        {
            "type": "TExtractorFlat",
            "note": "App with i18n key not nested, the messsage is the key. 
            Extract from `T('default message')`",
            "text_key": true,
            "root": "./example_app_t_flat",
            "extension_list": ["html"]
        },
        {
            "type": "TExtractorFlat",
            "note": "App with i18n key not nested, the messsage is the key encoded in md5. 
            Extract from `T('default message')`",
            "root": "./example_app_t_flat_md5",
            "extension_list": ["html"]
        },
    ],
    "debug": true // boolean debug mode wins over `--n`
}
```

## do the sync
will extract and upload the news on the server and download new translations from the server and save it in local file i18n json.

run shell `uggaugga_sync`

debug mode (only print)
run shell `uggaugga_sync --n`


## Come funziona la sync

Estrae dal codice le chiavi marcate con marcatori speciali usando gli `extractors` definiti nel file `uggaugga_config.json`. 
Per esempio se si usa un **TExtractor** estrarrà dal codice tutte le diciture `T('key','default')` ad esempio `T('app.title', 'greenApes')` e genera il file  i18n sotto la path `i18n_path` esempio: `./locales/i18n.json` che carica sul server UggaUgga.

Verranno rimosse dal server le chiavi che non sono presenti nell'ultima estrazione, verranno aggiunte le nuove chiavi e mantenute le chiavi uguali con le vecchie traduzioni.

**NB**
NON si deve tradurre mai sul file json ma sempre su UggaUgga server, il client deve solo scrivere il codice con `T('mia_chiave', 'valore default')` e quando è pronto per il rilascio lancia il comando `uggaugga_sync` (vedi sopra) e poi va su ugga ugga a tradurre i nuovi testi. Una volta fatto rilancia il comando di `uggaugga_sync` per avere le traduzioni aggiornate in locale e poterle committare/rilasciare.

-------------------------------

# Configurazione su greenApes
- OGNI CLIENT USA IL SUO FILE (i18n_android.json, i18n_ios.jso, i18n_bigfoot.json, i18n_roots.json etc)

- I CLIENT (ios, webs, android, server) usando gli estrattori caricano tutte le lingue + `ORIGINAL` nel loro file, quest'ultima lingua riporta il valore di default delle chiavi.

- LE TRADUZIONI SI FANNO SUL SERVER NON SUL FILE

- IL Database usa un admin plugin per aggiungere le chiavi

- La lingua di default del sistema può essere una a scelta, ad esempio "en" che se non trova la lingua scelta si mostra en, se non trova en si mostra ORIGINAL

```json
{
    "OGIRINAL": {
        "key1": "default value"
    },
    "it": {
        "key1": ""
    },
    "en": {
        "key1": ""
    }
}
```

## client auto extractor

1)  **extract** Uno script estrae dal codice le stringhe `T('key_flatten', 'default')` e crea un json per ogni lingua *(vedi esempio 1)*:
    -   per la lingua `ORIGINAL` riporta la gerarchia di chiavi di `key_flatten` e assegna il valore di `default` oppure stringa vuota.
    - per le altre lingue riporta la gerarchia di chiavi di `key_flatten` e assegna il valore stringa vuota sempre (da tradurre su uggaugga)
2) **download remote** scarico il remoto e faccio il **merge** usando come base di partenza il nuovo i18n json generato (non il remoto):
    - **ORIGINAL** la lingua original rimane quella del json appena generato
    - **ALTRE LINGUE** le chiavi rimangono quelle del nuovo json appena generato ma se trovo il valore di quella chiave nella versione remota, uso il valore delle remoto.
        - (in quanto il valore generato per le lingue è sempre stringa vuota e quindi voglio mantenere le traduzioni fatte in remoto. Se il client traduce toccando il file in locale (NON LO DEVE FARE) perde le traduzioni fatte)
3) **update local** salvo il json nell'i18n locale)
4) **upload** carico il file locale sul server

*esempio 1*: 
il client che agiste sul file `bigfoot.json` ha nel codice solo la stringa `T('campaign.filters.completed', 'Completeds')`. Viene generato:

```json
/bigfoot.json
{
    "ORIGINAL": {
        "campaign":{
            "filters": {
                "completed": "Completeds"
            }
        },
    },
    "it": {
        "campaign":{
            "filters": {
                "completed": "" // da tadurre
            }
        },
    },
    "en": {
        "campaign":{
            "filters": {
                "completed": "" // da tadurre
            }
        },
    }
}
```

## server auto extractor

1) **extract** xgettext estrae tutti i file .py e li scrive in .po
2) **po to json** uno script trasforma il file .po in un json e aggiorna l'I18n json locale creando tutte le lingue e usando come chiave l'hash md5 della stringa (vedi *esempio 2*).
nella lingua `ORIGINAL` viene riportato il valore di default, per le altre lingue viene riportata stringa vuota (da tradurre su uggaugga).
3) vedi *client auto extractor* dal punto 2) compreso, in poi

*esempio 2*
```json
{
    "ORIGINAL": {
        "server": {
            "diaodj001iwiwadjasodj": "sample string"
        }
    }
}
```

## admin plugin

1) accanto a ogni field admin da tradurre appare il plugin che è un link con la chiave desiderata da creare su ugga ugga
2) quando l'admin entra e clicca sul plugin, atterra su uggaugga che gli chiede di tradurre la chiave per le varie lingue (ORIGINAL compresa, deve essere inserita)