# MaimaiDataConverter

Migrate your data from maimaidx-prober to your local/community maimai server.

Requires a legit maimai install.

DISCLAIMER:

This software provides as-is and we are not responsable for any behaviour by you.

USE IT AT YOUR OWN RISK.

## Usage:
```bash
usage: app.py [-h] [--debug DEBUG] [--installPath INSTALLPATH] [--refreshCache REFRESHCACHE] [--csvPath CSVPATH] [--jsonPath JSONPATH]

options:
  -h, --help            show this help message and exit
  --debug DEBUG
  --installPath INSTALLPATH
  --refreshCache REFRESHCACHE
  --csvPath CSVPATH
  --jsonPath JSONPATH
```
Example:
`python3 app.py --installPath /opt/SDEZ1.35/Sinmai_Data/ --csvPath /opt/Downloads/乐谱.csv --jsonPath /opt/a.json`
