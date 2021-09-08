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

### Mandatory flags to provide

- API specific `--api` endpoint & `--token` values
- DB specific `--db_user` & `--db_pass` (and optionally `--db_host`)

### Other useful flags

- `--verbosity` sets the amount of output provided. By default `INFO` level data is printed (value of `0`). Set to `-1` to suppress `INFO` and only print found new names.
- `--batchsize` will be used to batch API queries. By default 5 but your API provider may recommend a specific value.
- `--loop_interval` will cause the tool to query continuously every N hours defined by this parameter. By default only a single query is made.

### Considerations

- The API will not be queried unless missing names are found.
- If missing names are found, `--batchsize` will be used to batch API queries. Your API provider may recommend a specific value.
- See `sample.flags` for a sample set of mandatory flags. A flagfile such as the sample is the simplest way to run;
    ```
    namepull --flagfile=sample.flags
    ```
### Flags from ENV variables

You can also use env variables to provide flag values. This can be handy for the docker image to provide secrets in a safe manner:
- NAMEPULL_API
- NAMEPULL_TOKEN
- NAMEPULL_DB
- NAMEPULL_DB_HOST
- NAMEPULL_DB_PASS
- NAMEPULL_DB_USER
- NAMEPULL_BATCHSIZE
- NAMEPULL_LOOP_INTERVAL

### Continuous queries

- You can specify an optional `--loop_interval` value in hours.
- The value will receive a random jitter addition up to a max of +5%.
