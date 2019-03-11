#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :

import asyncio
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import attr
from absl import app, logging as log
from bs4 import BeautifulSoup

from aiohttp import ClientSession
from comm import fetch, init_logging

HYMNS_INDEX_URL = "http://mvcccit.org/Legacy/chinese/?content=it/song.htm"
DOWNLOAD = Path("download/mvccc")
PROCESSED = Path("processed/mvccc")


@attr.s
class Hymn:
    name: str = attr.ib()
    no: str = attr.ib()
    url: str = attr.ib()
    filepath: Path = attr.ib(init=False)

    def __attrs_post_init__(self):
        assert self.url.endswith(".pptx")
        self.filepath = PROCESSED / f"{self.no}_{self.name}.pptx"


async def index(session: ClientSession, url: str) -> List[Hymn]:
    t = urlparse(url)
    index_path = DOWNLOAD / Path(t.path).name
    # check cache, if exists use cache
    if index_path.exists():
        log.info(f"{index_path} exists and use it as cache.")
        with index_path.open("rb") as f:
            content = f.read()
    else:
        status, content = await fetch(session, url)
        assert status == 200
        with index_path.open("wb") as out:
            out.write(content)

    text = content.decode()
    soup = BeautifulSoup(text, "html.parser")
    table = soup.find("table", attrs={"id": "mytable"})
    hymns = []
    for tr in table.findAll("tr"):
        tds = tr.findAll("td")
        if len(tds) != 3:
            continue
        no = tds[0].text.strip()
        if len(no) < 3 and no.isdigit():
            no = f"{int(no):03d}"
        name = tds[1].text.strip()
        link = tds[2].a["href"]
        hymn = Hymn(name=name, no=no, url=link)
        hymns.append(hymn)

    return hymns


async def download(session: ClientSession, hymn: Hymn):
    if hymn.filepath.exists():
        log.debug(f"{hymn.filepath} is already downloaded.")
        return

    log.debug(f"downloading to {hymn.filepath} ...")
    try:
        status, content = await fetch(session, hymn.url)
        assert status == 200
        with hymn.filepath.open("wb") as f:
            f.write(content)
    except AssertionError:
        log.exception(f"failed to download {hymn.filepath}")


async def download_pptx():
    async with ClientSession() as session:
        hymns = await index(session, HYMNS_INDEX_URL)
        tasks = [download(session, hymn) for hymn in hymns]
        await asyncio.wait(tasks)


def main(argv):
    del argv
    DOWNLOAD.mkdir(exist_ok=True, parents=True)
    init_logging()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_pptx())


if __name__ == "__main__":
    app.run(main)
