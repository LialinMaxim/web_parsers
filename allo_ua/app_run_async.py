import asyncio
import json
import time

import aiohttp
from sqlalchemy import update

from sqlite_master import session_factory, AlloUaTips

URL = 'https://allo.ua/ua/catalogsearch/ajax/suggest/?currentTheme=chunk_process&currentLocale=uk_UA'
EN = 'abcdefghijklmnopqrstuvwxyz'
RU = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
EMPTY = ['']
CHUNK = 100  # queries in one moment

session = session_factory()
loop = asyncio.get_event_loop()


async def get_response(allo_obj):
    async with aiohttp.ClientSession(json_serialize=json.dumps) as session:
        async with session.post(URL, data={'q': allo_obj.request}) as response:
            return allo_obj, await response.text()


def update_db(allo_obj, res):
    def j_dump(json_data):
        return json.dumps(json_data, ensure_ascii=False)

    if len(res) == 0:  # case when response is []
        stmt = update(AlloUaTips).where(AlloUaTips.id == allo_obj.id).values(
            complete=True,
        )
        session.execute(stmt)
    else:
        stmt = update(AlloUaTips).where(AlloUaTips.id == allo_obj.id).values(
            response_query=j_dump(res.get('query', [])),
            response_products=j_dump(res.get('products', [])),
            response_categories=j_dump(res.get('categories', [])),
            complete=True,
        )
    session.execute(stmt)
    session.commit()


def chunk_process(queries_list):
    res = []
    start = time.time()
    try:
        coroutines = [loop.create_task(get_response(allo)) for allo in queries_list]
        res = loop.run_until_complete(asyncio.wait(coroutines))
    finally:
        for r in res[0]:
            allo_obj, new_data = r.result()
            update_db(allo_obj, json.loads(new_data))
            print(allo_obj.id, allo_obj.request, 'DONE', new_data)
        print(f"Runtime of {CHUNK} requests: {time.time() - start}")


def run_parser():
    def get_chunk():
        return session.query(AlloUaTips).filter(AlloUaTips.complete.is_(False)).limit(CHUNK)

    queries_list = get_chunk()
    while queries_list:
        print('\n-- new chunk --\n')
        chunk_process(queries_list)
        queries_list = get_chunk()

    print('PARSING COMPLETE :)')
    loop.close()


def create_empty_db(sequence):
    """
    Creating an empty database with all combinations of queries
    :param sequence: EN or RU alphabet string
    :return: None
    """

    def query_param_generator(x, y, z):
        """
        :param x: long string
        :param y, z: long string or ['']
        :return: str
        """
        for _x in x:
            for _y in y:
                for _z in z:
                    yield _x + _y + _z

    def create_empty_allo_obj(query_str):
        session.add(AlloUaTips(request=query_str, query=[], products=[], categories=[]))

    # Single letter combinations
    for query in query_param_generator(sequence, EMPTY, EMPTY):
        create_empty_allo_obj(query)

    # Two-letter combinations
    for query in query_param_generator(sequence, sequence, EMPTY):
        create_empty_allo_obj(query)

    # Three letter combinations
    for query in query_param_generator(sequence, sequence, sequence):
        create_empty_allo_obj(query)

    session.commit()
    print(f'Created all combinations with -- {sequence}')


if __name__ == '__main__':
    """
    Create a database only once, otherwise there will be an error but nothing bad will happen.
    In case of error, just restart. (but turn of DB creation bellow
    """
    create_empty_db(RU)
    create_empty_db(EN)

    run_parser()
