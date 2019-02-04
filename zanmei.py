#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :
import re
import shutil
from pathlib import Path
from typing import Dict

import attr
import requests
from absl import app
from absl import logging as log
from bs4 import BeautifulSoup

# 教会圣诗 Hymns for God's People
HYMNS_INDEX_URL = "https://www.zanmeishi.com/songbook/hymns-for-gods-people.html"
ZANMEI_HOMEPAGE = "https://www.zanmeishi.com"

DOWNLOAD = Path("download")


@attr.s
class Hymn:
    name: str = attr.ib()
    no: int = attr.ib()
    url: str = attr.ib()
    filepath: Path = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.filepath = DOWNLOAD / f"{self.no:03d}_{self.name}.png"


def index(url: str) -> Dict[str, Hymn]:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    div = soup.find("div", attrs={"class": "sbtablist"})
    for li in div.findAll("li"):
        no = re.search(r"\d+", li.text).group()
        name = li.a["title"].replace("查看歌谱", "")
        hymn = Hymn(name=name, no=int(no), url=f"{ZANMEI_HOMEPAGE}{li.a['href']}")
        yield hymn


def download(hymn: Hymn):
    if hymn.filepath.exists():
        log.debug(f"{hymn} is already downloaded.")
        return

    log.debug(f"download {hymn} ...")
    r = requests.get(hymn.url)
    soup = BeautifulSoup(r.text, "html.parser")
    div = soup.find("div", attrs={"class": "img_tab"})
    img_url = div.a["href"]
    r = requests.get(img_url, stream=True)
    assert r.status_code == 200
    with hymn.filepath.open("wb") as f:
        shutil.copyfileobj(r.raw, f)


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


def main(argv):
    del argv
    DOWNLOAD.mkdir(exist_ok=True, parents=True)
    hymns = list(index(HYMNS_INDEX_URL))
    for hymn in hymns:
        try:
            download(hymn)
        except Exception:
            log.exception(f"failed to download {hymn}.")
    verify(DOWNLOAD, "*.png", len(hymns))


if __name__ == "__main__":
    app.run(main)
