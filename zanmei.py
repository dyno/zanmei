#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :

import asyncio
import re
from pathlib import Path
from typing import List

import attr
from absl import app, logging as log
from bs4 import BeautifulSoup
from hanziconv import HanziConv

from aiohttp import ClientSession
from comm import fetch, init_logging

# 教會聖詩 Hymns for God's People
HYMNS_INDEX_URL = "https://www.zanmeishi.com/songbook/hymns-for-gods-people.html"
ZANMEI_HOMEPAGE = "https://www.zanmeishi.com"

DOWNLOAD = Path("download/zanmei")


@attr.s
class Hymn:
    name: str = attr.ib()
    no: int = attr.ib()
    url: str = attr.ib()
    filepath: Path = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.filepath = DOWNLOAD / f"{self.no:03d}_{self.name}.png"


async def index(session: ClientSession, url: str) -> List[Hymn]:
    status, content = await fetch(session, url)
    text = content.decode()
    soup = BeautifulSoup(text, "html.parser")
    div = soup.find("div", attrs={"class": "sbtablist"})
    hymns = []
    for li in div.findAll("li"):
        no = re.search(r"\d+", li.text).group()
        name = li.a["title"].replace("查看歌谱", "")
        name = HanziConv.toTraditional(name)
        hymn = Hymn(name=name, no=int(no), url=f"{ZANMEI_HOMEPAGE}{li.a['href']}")
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
        text = content.decode()
        soup = BeautifulSoup(text, "html.parser")
        div = soup.find("div", attrs={"class": "img_tab"})
        img_url = div.a["href"]
        status, content = await fetch(session, img_url)
        assert status == 200
        with hymn.filepath.open("wb") as f:
            f.write(content)
    except AssertionError:
        log.exception(f"failed to download {hymn.filepath}")


def verify(filepath: Path, glob: str, total: int):
    path_list = list(filepath.glob(glob))
    downloaded = list(sorted(path.name.split("_", 1)[0] for path in path_list))
    expected = [f"{no:03d}" for no in range(1, total + 1)]
    missing = ["493", "494", "495"]
    log.warn(f"{missing} are missing from {HYMNS_INDEX_URL}. they are all in 492.")
    for no in missing:
        expected.remove(no)
    assert all((a == b) for a, b in zip(downloaded, expected))
    assert len(path_list) == total


async def download_image_copy():
    async with ClientSession() as session:
        hymns = await index(session, HYMNS_INDEX_URL)
        tasks = [download(session, hymn) for hymn in hymns]
        await asyncio.wait(tasks)
        verify(DOWNLOAD, "*.png", len(hymns))


def main(argv):
    del argv
    DOWNLOAD.mkdir(exist_ok=True, parents=True)
    init_logging()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_image_copy())


if __name__ == "__main__":
    app.run(main)
