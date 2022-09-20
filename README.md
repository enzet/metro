# Metro

[Wikidata](https://wikidata.org) parser for transport networks.

## Example run

To parse Prague metro system one should specify system Wikidata item
([Q190271](https://www.wikidata.org/wiki/Q190271) for Prague Metro) and
arbitrary station Wikidata item
([Q1877386](https://www.wikidata.org/wiki/Q1877386) for Florenc metro station).

```shell
python -m metro --system 190271 --station 1877386
```

## Output

Result will be in `out/metro.json` file with the following structure:

```json
{
    "id": "<TEXT IDENTIFIER>",
    "stations": ["<STATION STRUCTURE>"],
    "lines": ["<LINE STRUCTURE>"]
}
```

### Station structure

```json
{
    "id": "<LINE IDENTIFIER>/<STATION SHORT IDENTIFIER>",
    "line": "<LINE IDENTIFIER>",
    "names": {
        "<LANGUAGE>": "<NAME>"
    },
    "open_time": "",
    "geo_positions": ["<LATITUDE>", "<LONGITUDE>"],
    "connections": [
        {
            "to": "<OTHER STATION IDENTIFIER>",
            "type": "<CONNECTION TYPE>"
        }
    ],
    "site_links": [
        {
            "<SITE>": "<PAGE NAME>"
        }
    ]
}
```

### Line structure

```json
{
    "id": "<LINE IDENTIFIER>/<STATION SHORT IDENTIFIER>",
    "names": {
        "<LANGUAGE>": "<NAME>"
    },
    "color": "<LINE COLOR>"
}
```
