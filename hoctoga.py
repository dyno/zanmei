#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :

import asyncio
import os
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZipFile

from absl import app, flags, logging as log
from bs4 import BeautifulSoup

import aiohttp
from comm import TOTAL, fetch, init_logging

LYRICS_URL_TEMPLATE = "http://www.hoctoga.org/Chinese/lyrics/hymn/hymn-{idx:03d}.htm"
PPT_URL_BASE = "http://www.hoctoga.org/Chinese/lyrics/hymn/"

DOWNLOAD = Path("download/hoctoga")

FLAGS = flags.FLAGS


def extract_lyrics_and_ppt_link(text, index):
    soup = BeautifulSoup(text, "html.parser")
    trs = soup.find("table").findAll("tr")

    title = trs[0].text.strip()

    p_text = trs[1].p.text
    lines = map(str.strip, p_text.splitlines())
    raw_text = "\n".join(lines)
    raw_path = DOWNLOAD / f"{index:03d}_{title}.raw.txt"
    with raw_path.open("w") as out:
        log.info(f"extract lyrics to {raw_path}")
        out.write(raw_text)

    errata_path = DOWNLOAD / f"{index:03d}_{title}.errata.txt"
    if errata_path.exists():
        log.warn(f"{errata_path} exists, use it instead.")
        with errata_path.open("r") as f:
            p_text = f.read()

    ppt_link = PPT_URL_BASE + trs[1].a["href"]
    return raw_text, ppt_link


async def download_and_extract_ppt(ppt_zip_link, index):
    log.info(f"processing {ppt_zip_link}")
    t = urlparse(ppt_zip_link)
    assert t.path.endswith("hymn-{index:03}.zip")

    ppt_zip_path = DOWNLOAD / Path(t.path).name
    if ppt_zip_path.exists():
        log.info(f"{ppt_zip_path} exists. use it as cache.")
        with ppt_zip_path.open("rb") as f:
            content = f.read()
    else:
        ppt_missing_path = DOWNLOAD / f"{Path(t.path).name}.missing"
        if ppt_missing_path.exists():
            log.warn(f"{ppt_missing_path} exists. stop.")
            return
        status, content = await fetch(ppt_zip_link)
        if status == 200:
            with ppt_zip_path.open("wb") as out:
                out.write(content)
        elif status == 404:
            log.warn(f"write {ppt_missing_path}. stop.")
            ppt_missing_path.open("wb").close()
            return
        else:
            log.error(f"status={status}")
            return

    log.info(f"extract {ppt_zip_path}")
    zf = ZipFile(BytesIO(content))
    infolist = zf.infolist()
    assert len(infolist) == 1


async def download_lyrics_with_ppt():
    async with aiohttp.ClientSession() as session:
        for idx in range(1, TOTAL + 1):
            lyrics_url = LYRICS_URL_TEMPLATE.format(idx=idx)
            t = urlparse(lyrics_url)
            assert t.path.endswith(f"hymn-{idx:03d}.htm")
            lyrics_path = DOWNLOAD / Path(t.path).name
            try:
                # check cache, if exists use cache
                if lyrics_path.exists():
                    log.info(f"{lyrics_path} exists and use it as cache.")
                    with lyrics_path.open("rb") as f:
                        content = f.read()
                else:
                    lyrics_missing_path = DOWNLOAD / f"{Path(t.path).name}.missing"
                    if lyrics_missing_path.exists():
                        log.warn(f"{lyrics_missing_path} exists. continue.")
                        continue
                    status, content = await fetch(session, lyrics_url)
                    if status == 200:
                        with lyrics_path.open("wb") as out:
                            out.write(content)
                    elif status == 404:
                        lyrics_missing_path.open("wb").close()
                        log.warn(f"write {lyrics_missing_path}. continue.")
                        continue
                    else:
                        log.error(f"status={status}")

                # extract the lyrics and the ppt link
                try:
                    log.info(f"decoding content for {lyrics_url}")
                    text = content.decode("big5", errors="strict")
                except UnicodeDecodeError:
                    log.warn(f"ignore decoding errors for {lyrics_url}")
                    text = content.decode("big5", errors="ignore")

                raw_text, ppt_link = extract_lyrics_and_ppt_link(text, idx)
                download_and_extract_ppt(ppt_link, idx)
            except Exception:  # NOQA
                log.exception(f"exception for {lyrics_url}")


def main(argv):
    del argv

    init_logging()
    DOWNLOAD.mkdir(exist_ok=True, parents=True)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_lyrics_with_ppt())


if __name__ == "__main__":
    app.run(main)
