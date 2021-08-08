# Namepull for MAD
Retrieve gym names from a compatible API

## Prereqs
- Python3.7 minimum. (aiohttp compatibility.)
- Already set up MAD DB with gyms with unknown names.

## Installation
### Just use it
```
pip3 install namepull
```
### Development
```
# Get python-poetry:
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python3 -
# install deps in a venv and run:
poetry run namepull
```

## Usage
All needed data is given as cli flags.
- API endpoint must be provided with `--api`
- API token must be provided with `--token`
- DB data must be provided with `--db_user` & `--db_pass` (and optionally `--db_host`)
- See `sample.flags` for a sample set of mandatory flags. A flagfile such as the sample is the simplest way to run;
    ```
    namepull --flagfile=sample.flags
    ```
