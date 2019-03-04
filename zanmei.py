#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :

import asyncio
import re
from pathlib import Path
from typing import List
from urllib.parse import urlparse

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
    div = soup.find("div", attrs={"class": "sbtablist"})
    hymns = []
    for li in div.findAll("li"):
        no = re.search(r"\d+", li.text).group()
        name = li.a["title"].replace("查看歌谱", "")
        name = (
            HanziConv.toTraditional(name)
            .replace("傢", "家")
            .replace("山巔", "山嶺")
            .replace("嚮", "向")
            .replace("恒", "恆")
            .replace("我真希奇", "我神你是何等奇妙")
            .replace("榖中百閤花", "谷中百合花")
            .replace("渡過", "度過")
            .replace("禰", "祢")
            .replace("萬福思源", "萬福恩源")
            .replace("裏", "裡")
            .replace("贊", "讚")
            .replace("起來，宗主信徒", "齊來，宗主信徒")
            .replace("迴", "回")
            .replace("隻", "只")
            .replace("麯", "曲")
            .replace("籍我", "藉我")
        )
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
