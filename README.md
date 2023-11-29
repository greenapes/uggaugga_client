# api per i client

## installation

To get latest version run `pip3 install git+https://github.com/greenapes/uggaugga_client.git@master#egg=uggaugga_client --upgrade`

## project config

run `uggaugga init`

This command create the file `uggaugga_config.json`



**uggaugga_config.json SPECS**
```js
{
    /* 
        REQUIRED 
        the name of your project is the file uploaded to the server
    */
    "namespace": "sample_app", 
    
    /*
        REQUIRED
        list of supported langs (2 letter format)
    */
    "langs": ["it", "en"],
    
    /*
        OPTIONAL

        - if not set the default strings values goes 
        under and addictional language called 'ORIGINAL'.
        When you dont know where is the original language
        is usefull.

        - if is set the default strings values goes under 
        this language
    */
    "default_lang": "en",
    
    /*
        OPTIONAL default 'json'

        Is the format of the output file.
        
        Can be:
        - 'json': i18n.json format (nested or not)
        - 'xml_android' is for native android app create .xml files under `i18n_path`
        - 'strings_ios' is for native ios app create .strings files unedr `i18n_path`
    */
    "export_format": "json",
    /*
        REQUIRED
        is the path where save the output file.

        If the `export_format` is not or 'json' the
        `i18n_path` must be a file path ends with '.json'

        If the `export_format` is 'xml_android' or 'strings_ios'
        the `i18n_path` must be a folder path
    */
    "i18n_path": "./locales/i18n.json",

    /*
        OPTIONAL default false
        if is set the sync only print, not upload, not save local

        boolean debug mode wins over `--n`
    */
    "debug": false

    /*
        OPTIONAL default false
        if is set the sync not upload to remote, only save local
    */
    "disable_upload": false
    
    /*
        REQUIRED
        UggaUgga server connection infos
    */
    "server": {
        // the server base url
        "url": "<my uggaugga server url>",
        // the given public
        "public_key": "<my uggaugga server public key>",
        // the given secret
        "secret_key": "<my uggaugga server secret key>"
    },

    /*
        REQUIRED
        A list of code extractors to automatically extract
        the strings from code files.
    */
    "extractors": [
        /*
        TExtractor

        Extract  from `T('my.key', 'default value')` or use custom_regex.

        Nested, not flat
        */
        {
            // REQUIRED
            "type": "TExtractor",
            
            /* 
                REQUIRED
                This extractor search only under this
                root path
            */
            "root": "./example_app_t",

            /*
                REQUIRED
                The list of the file extentions to check
            */
            "extention_list": ["js", "ts", "jsx", "tsx"],

            /*
                OPTIONAL
                A regex to extract code, must have 2 groups, the first for the key, the second for the default value
            */
           "custom_regex": "{{\\s*T\\s+['\"](.*)['\"]\\s*['\"](.*?)['\"]\\s*}}",
        }
        /*
            TExtractorFlat
            Extract from `T('my string')` or use custom_regex.

            Only flat, not nested.
        */
        {
            // REQUIRED
            "type": "TExtractorFlat",

            /* 
                REQUIRED
                This extractor search only under this
                root path
            */
            "root": "./example_app_t_flat_md5",

            /*
                REQUIRED
                The list of the file extentions to check
            */
            "extension_list": ["html"],

            /*
                OPTIONAL:
                and optional parent key under goes all
                translations
            */
            "I18n_parent_key": "server_strings"

            /*
                OPTIONAL
                A regex to extract code, must have 1 group for
                the default value
            */
            "custom_regex": "translate\\s>(.*)<"
        },
        /*
        XgettexExtractor

        Use linux xgettext library to extract strings 
        from code and genereate .po that we converted 
        in i18n format for you.

        Extract from `_('my string')`.

        Only flat, not nested.
        */
        {
            // REQUIRED
            "type": "XgettexExtractor",
            /* 
                REQUIRED
                This extractor search only under this
                root path
            */
            "root": "./example_app_xgettext",
            /*
                REQUIRED
                xgettext extension field
            */
            "extension": "py",
            /*
                REQUIRED
                xgettext language field
            */
            "language": "python",
            /*
                OPTIONAL:
                and optional parent key under goes all
                translations
            */
            "I18n_parent_key": "server_strings"
        }
    ]
}
```

## do the sync
will extract and upload the news on the server and download new translations from the server and save it in local file i18n json.

run shell `uggaugga sync`

debug mode (only print)
run shell `uggaugga sync --n`
