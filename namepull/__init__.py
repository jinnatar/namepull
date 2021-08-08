import sys
import asyncio
import aiohttp
from aiohttp import ClientSession
from absl import app, flags, logging
import json
import pymysql
from sql import *

FLAGS = flags.FLAGS

flags.DEFINE_string('token', None, 'API token')
flags.DEFINE_string('db', 'mad', 'MAD DB name')
flags.DEFINE_string('db_pass', None, 'MAD DB password')
flags.DEFINE_string('db_user', None, 'MAD DB user')
flags.DEFINE_string('db_host', '127.0.0.1', 'MAD DB host')
flags.DEFINE_string('api', None, 'API endpoint')
flags.DEFINE_integer('batchsize', '5', 'Queries per request')

# API endpoint & token must be provided as flags
flags.mark_flag_as_required("token")
flags.mark_flag_as_required("api")
# DB credentials are also mandatory and have no reasonable defaults
flags.mark_flag_as_required("db_pass")
flags.mark_flag_as_required("db_user")


# Helper to yield finite ranges of an iterable to chunk up work into batches
def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


# Async json data downloader
async def download(url, data, session, method='POST', **kwargs) -> str:
    response = await session.request(method=method, url=url, json=data)
    response.raise_for_status()
    data = await response.json()
    return data


# download data -> store data
async def get_gyms(ids, **kwargs) -> None:
    url = '{api}?token={token}'.format(api=FLAGS.api, token=FLAGS.token)
    response = await download(url, ids, **kwargs)
    await store_gyms(response, **kwargs)


# Process received data into UPDATE statements & execute them
async def store_gyms(data, cursor, table, **kwargs) -> None:
    for gym in data:
        print(gym['name'])
        columns = [table.name]
        values = [gym['name']]
        if 'imageUrl' in gym and gym['imageUrl'] is not None:
            columns.append(table.url)
            values.append(gym['imageUrl'])
        update = table.update(where=table.gym_id == gym['id'],
                              columns=columns,
                              values=values)
        cursor.execute(*update)


# Retrieve unknown gyms, resolve them & store them
async def get_unknown_gyms():
    db = pymysql.connect(host=FLAGS.db_host,
                         user=FLAGS.db_user,
                         password=FLAGS.db_pass,
                         db=FLAGS.db,
                         cursorclass=pymysql.cursors.DictCursor)
    cursor = db.cursor()
    cursor.execute("SET sql_mode = 'ANSI_QUOTES'")

    gym = Table('gymdetails')
    select = gym.select(gym.gym_id)
    select.where = (gym.name == None) | (gym.name == 'unknown')
    cursor.execute(*select)
    ids = []
    for row in cursor.fetchall():
        ids.append(row['gym_id'])

    async with ClientSession() as session:
        tasks = []
        for i in batch(ids, FLAGS.batchsize):
            tasks.append(get_gyms(i, session=session, cursor=cursor,
                                  table=gym))
        await asyncio.gather(*tasks)
    db.commit()


# Wrap asyncio.run for easy compatibilty with absl.app
def main(argv):
    del argv
    asyncio.run(get_unknown_gyms())

# script endpoint installed by package
def run():
    app.run(main)

if __name__ == '__main__':
    run()
