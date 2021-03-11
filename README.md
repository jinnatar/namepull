# Namepull for MAD
Retrieve gym names from a compatible API

## Prereqs
- Python3.7 minimum. (aiohttp compatibility.)
- `pip3 install -r requirements.txt`
- Already set up MAD DB with gyms with unknown names.

## Usage
All needed data is given as cli flags.
- API endpoint must be provided with `--api`
- API token must be provided with `--token`
- DB data must be provided with `--db_user` & `--db_pass` (and optionally `--db_host`)
- See `sample.flags` for a sample set of mandatory flags. A flagfile such as the sample is the simplest way to run;
    ```
    python3.7 namepull.py --flagfile=sample.flags
    ```
