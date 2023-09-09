import asyncio
import os
from typing import Any, Dict, List, Optional, Sequence

import aiohttp
import backoff
import pymysql
from absl import app, flags, logging
from aiohttp import ClientSession
from pymysql.cursors import DictCursor
from sql import Table

FLAGS = flags.FLAGS

PREFIX = "NAMEPULL"

flags.DEFINE_string("api", os.getenv(f"{PREFIX}_API", None), "API endpoint")
flags.DEFINE_string("token", os.getenv(f"{PREFIX}_TOKEN", None), "API token")
flags.DEFINE_string("db", os.getenv(f"{PREFIX}_DB", "mad"), "MAD DB name")
flags.DEFINE_string(
    "db_host", os.getenv(f"{PREFIX}_DB_HOST", "127.0.0.1"), "MAD DB host"
)
flags.DEFINE_string("db_pass", os.getenv(f"{PREFIX}_DB_PASS", None), "MAD DB password")
flags.DEFINE_string("db_user", os.getenv(f"{PREFIX}_DB_USER", None), "MAD DB user")
flags.DEFINE_integer(
    "batchsize", os.getenv(f"{PREFIX}_BATCHSIZE", 5), "Queries per request"
)
flags.DEFINE_integer(
    "loop_interval",
    os.getenv(f"{PREFIX}_LOOP_INTERVAL", None),
    "Interval in hours to poll repeatedly. A random 5% jitter is applied.",
)


def not_null(value: Any) -> bool:
    return value is not None


# API endpoint & token must be provided
flags.register_validator(
    "token", not_null, message="API token must be set", flag_values=FLAGS
)
flags.register_validator(
    "api", not_null, message="API endpoint must be set", flag_values=FLAGS
)

# DB credentials are also mandatory and have no reasonable defaults
flags.register_validator(
    "db_pass", not_null, message="DB password must be set", flag_values=FLAGS
)
flags.register_validator(
    "db_user", not_null, message="DB user must be set", flag_values=FLAGS
)


# Helper to yield finite ranges of a sequence to chunk up work into batches
def batch(sequence: Sequence[str], n: int = 1) -> Any:
    length = len(sequence)
    for ndx in range(0, length, n):
        yield sequence[ndx : min(ndx + n, length)]


# Return a delay with a random percentage jitter added
def pct_jitter(value: float, multiplier: float) -> float:
    jitter: float = backoff.full_jitter(value * multiplier)
    return value + jitter


# Async json data downloader
@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_time=60, logger="absl")  # type: ignore
async def download(
    url: str,
    data: List[str],
    session: ClientSession,
    method: str = "POST",
) -> List[Optional[Dict[str, str]]]:
    response = await session.request(method=method, url=url, json=data)
    response.raise_for_status()
    result: List[Optional[Dict[str, str]]] = await response.json()
    return result


# download data -> store data
async def get_gyms(
    gym_ids: List[str], table: Table, cursor: DictCursor, session: ClientSession
) -> None:
    logging.debug(f"fetching {gym_ids}")
    url = f"{FLAGS.api}?token={FLAGS.token}"
    response = await download(url, gym_ids, session=session)
    if response:
        logging.debug(f"Got: {response}")
        diff = len(gym_ids) - len(response)
        if diff > 0:
            logging.warning(
                "Out of {len(gym_ids)} gyms in batch, {diff} were unknown to API provider."
            )
        gyms: List[Dict[str, str]] = response
        await store_gyms(gyms, table=table, cursor=cursor)
    else:
        logging.warning(f"All {len(gym_ids)} gyms in batch unknown to API provider.")


# Process received data into UPDATE statements & execute them
async def store_gyms(
    gyms: List[Dict[str, str]], cursor: DictCursor, table: Table
) -> None:
    for gym in gyms:
        print(gym["name"])
        columns = [table.name]
        values = [gym["name"]]
        if "imageUrl" in gym and gym["imageUrl"] is not None:
            columns.append(table.url)
            values.append(gym["imageUrl"])
        update = table.update(
            where=table.gym_id == gym["id"], columns=columns, values=values
        )
        cursor.execute(*update)


# Retrieve unknown gyms, resolve them & store them
async def get_unknown_gyms() -> None:
    logging.debug("Polling for unknown gyms")
    db = pymysql.connect(
        host=FLAGS.db_host,
        user=FLAGS.db_user,
        password=FLAGS.db_pass,
        db=FLAGS.db,
        cursorclass=DictCursor,
    )
    cursor: DictCursor = db.cursor()
    cursor.execute("SET sql_mode = 'ANSI_QUOTES'")

    gym = Table("gymdetails")
    select = gym.select(gym.gym_id)
    select.where = (gym.name == None) | (gym.name == "unknown")  # noqa: E711
    cursor.execute(*select)
    ids: List[str] = []
    for row in cursor.fetchall():
        ids.append(row["gym_id"])

    if ids:
        logging.info(f"Found {len(ids)}")
        async with ClientSession() as session:
            tasks = []
            for seq in batch(ids, FLAGS.batchsize):
                tasks.append(get_gyms(seq, session=session, cursor=cursor, table=gym))
            await asyncio.gather(*tasks)
        db.commit()


# Repeatedly query for missing names on an interval in hours
async def looper(interval: int) -> None:
    logging.info(f"Querying every {interval} hours")
    interval_seconds = interval * 60 * 60
    while True:
        logging.info("Querying now...")
        await get_unknown_gyms()
        jittered_interval = pct_jitter(interval_seconds, 0.05)
        logging.info(f"Sleeping until next iteration in {jittered_interval:.2f}s")
        await asyncio.sleep(jittered_interval)


# Wrap asyncio.run for easy compatibilty with absl.app
def main(argv: List[str]) -> None:
    del argv
    if FLAGS.loop_interval:
        asyncio.run(looper(FLAGS.loop_interval))
    else:
        asyncio.run(get_unknown_gyms())


# script endpoint installed by package
def run() -> None:
    app.run(main)


if __name__ == "__main__":
    run()
