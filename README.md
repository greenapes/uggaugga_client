# api per i client

run shell `python3 ./uggaugga_sync.py --name=android`

**doc**
Estrae dal codice le chiavi marcate con `T('key','default')` ad esempio `T('app.title', 'greenApes')` e genera il file `I18N/android.json` che carica sul server UggaUgga.

Verranno rimosse le chiavi che sono state rimosse, verranno aggiunte le nuove e mantenute le vecchie traduzioni.

**NB**
NON si deve tradurre mai sul file json ma sempre su UggaUgga server, il client deve solo scrivere il codice con `T('mia_chiave', 'valore default')` e quando è pronto per il rilascio lancia il comando di sync (vedi sopra) e poi va su ugga ugga a tradurre i nuovi testi. Una volta fatto rilancia il comando di syn per avere le traduzioni in locale e poterle committare/rilasciare.


# Come UggaUgga funziona NB
- OGNI CLIENT USA IL SUO FILE (android.json, ios.jso, bigfoot.json, roots.json)

- I CLIENT (ios, webs, android, server) usando gli estrattori caricano tutte le lingue + `ORIGINAL` nel loro file, quest'ultima riporta il valore di default delle chiavi.

- LE TRADUZIONI SI FANNO SUL SERVER NON SUL FILE

- IL Database usa admin plugin per aggiungere le chiavi


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