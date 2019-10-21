#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :

import asyncio
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import attr
from absl import app, flags, logging as log
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from hymns import fetch

FLAGS = flags.FLAGS
HYMNS_INDEX_URL = "http://mvcccit.org/Legacy/chinese/?content=it/song.htm"


@attr.s
class Hymn:
    name: str = attr.ib()
    no: str = attr.ib()
    url: str = attr.ib()


def _path(hymn: Hymn, download_basepath: Optional[Path] = None) -> Path:
    if download_basepath is None:
        download_basepath = Path(FLAGS.download_basedir)

    assert hymn.url.endswith(".pptx")
    path = download_basepath / f"{hymn.no}_{hymn.name}.pptx"

    return path


async def index(session: ClientSession, url: str, download_basepath: Optional[Path] = None) -> List[Hymn]:
    if download_basepath is None:
        download_basepath = Path(FLAGS.download_basedir)

    t = urlparse(url)
    index_path = download_basepath / Path(t.path).name
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


async def download(session: ClientSession, hymn: Hymn) -> None:
    if _path(hymn).exists():
        log.debug(f"{_path(hymn)} is already downloaded.")
        return

    log.debug(f"downloading to {_path(hymn)} ...")
    try:
        status, content = await fetch(session, hymn.url)
        assert status == 200
        with _path(hymn).open("wb") as f:
            f.write(content)
    except AssertionError:
        log.exception(f"failed to download {_path(hymn)}")


async def download_pptx() -> None:
    async with ClientSession() as session:
        hymns = await index(session, HYMNS_INDEX_URL)
        tasks = [download(session, hymn) for hymn in hymns]
        await asyncio.wait(tasks)


if __name__ == "__main__":
    from base import initialize_logging

    flags.DEFINE_string("download_basedir", "download/mvccc", "basedir of downloaded files")

    def main(_):
        initialize_logging()
        download_basepath = Path(FLAGS.download_basedir)
        download_basepath.mkdir(exist_ok=True, parents=True)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(download_pptx())

    app.run(main)
