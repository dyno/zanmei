#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :

import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

from absl import app, logging as log
from bs4 import BeautifulSoup

import aiohttp
from comm import TOTAL, fetch, init_logging, zip_blank_lines

LYRICS_URL_TEMPLATE = "http://www.hoc5.net/service/hymn{level}/{idx:03d}.htm"
DOWNLOAD = Path("download/hoc5")
PROCESSED = Path("processed/hoc5")


def extract_lyrics(text, index):
    soup = BeautifulSoup(text, "html.parser")

    title = soup.title.text
    title = re.sub("^[0-9 ]*", "", title).strip()

    table = soup.find("table")
    lines = zip_blank_lines(map(str.strip, table.text.splitlines()))
    raw_text = "\n".join(lines)
    raw_path = PROCESSED / f"{index:03d}_{title}.raw.txt"
    with raw_path.open("w") as out:
        log.info(f"extract lyrics to {raw_path}")
        out.write(raw_text)

    errata_path = PROCESSED / f"{index:03d}_{title}.errata.txt"
    if errata_path.exists():
        log.warn(f"{errata_path} exists, use it instead.")
        with errata_path.open("r") as f:
            raw_text = f.read()

    return raw_text


async def download_and_extract_lyrics(session, idx):
    level = idx // 100
    lyrics_url = LYRICS_URL_TEMPLATE.format(level=level, idx=idx)
    t = urlparse(lyrics_url)
    assert t.path.endswith(f"hymn{level}/{idx:03d}.htm")
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
                return
            status, content = await fetch(session, lyrics_url)
            if status == 200:
                with lyrics_path.open("wb") as out:
                    out.write(content)
            elif status == 404:
                lyrics_missing_path.open("wb").close()
                log.warn(f"write {lyrics_missing_path}. continue.")
                return
            else:
                log.error(f"status={status}")

        # extract the lyrics
        try:
            log.info(f"decoding content for {lyrics_url}")
            text = content.decode()
        except UnicodeDecodeError:
            log.warn(f"ignore decoding errors for {lyrics_url}")
            text = content.decode("big5", errors="ignore")

        extract_lyrics(text, idx)
    except Exception:  # NOQA
        log.exception(f"exception for {lyrics_url}")


async def process_hymns():
    async with aiohttp.ClientSession() as session:
        tasks = [download_and_extract_lyrics(session, idx) for idx in range(1, TOTAL + 1)]
        await asyncio.wait(tasks)


def main(argv):
    del argv

    init_logging()
    DOWNLOAD.mkdir(exist_ok=True, parents=True)
    PROCESSED.mkdir(exist_ok=True, parents=True)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_hymns())


if __name__ == "__main__":
    app.run(main)
