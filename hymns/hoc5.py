#!/usr/bin/env python3

import asyncio
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from absl import app, flags, logging as log
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from hymns import TOTAL, fetch, zip_blank_lines

FLAGS = flags.FLAGS
LYRICS_URL_TEMPLATE = "http://www.hoc5.net/service/hymn{level}/{idx:03d}.htm"


def extract_lyrics(text: str, index: int, processed_basepath: Optional[Path] = None) -> str:
    if processed_basepath is None:
        processed_basepath = Path(FLAGS.processed_basedir)

    soup = BeautifulSoup(text, "html.parser")

    title = soup.title.text
    title = re.sub("^[0-9 ]*", "", title).strip()

    table = soup.find("table")
    lines = zip_blank_lines(map(str.strip, table.text.splitlines()))
    raw_text = "\n".join(lines)
    raw_path = processed_basepath / f"{index:03d}_{title}.raw.txt"
    with raw_path.open("w") as out:
        log.info(f"extract lyrics to {raw_path}")
        out.write(raw_text)

    errata_path = processed_basepath / f"{index:03d}_{title}.errata.txt"
    if errata_path.exists():
        log.warn(f"{errata_path} exists, use it instead.")
        with errata_path.open("r") as f:
            raw_text = f.read()

    return raw_text


async def download_and_extract_lyrics(
    session: ClientSession, idx: int, download_basepath: Optional[Path] = None
) -> None:
    if download_basepath is None:
        download_basepath = Path(FLAGS.download_basedir)

    level = idx // 100
    lyrics_url = LYRICS_URL_TEMPLATE.format(level=level, idx=idx)
    t = urlparse(lyrics_url)
    assert t.path.endswith(f"hymn{level}/{idx:03d}.htm")
    lyrics_path = download_basepath / Path(t.path).name
    try:
        # check cache, if exists use cache
        if lyrics_path.exists():
            log.info(f"{lyrics_path} exists and use it as cache.")
            with lyrics_path.open("rb") as f:
                content = f.read()
        else:
            lyrics_missing_path = download_basepath / f"{Path(t.path).name}.missing"
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


async def process_hymns() -> None:
    async with ClientSession() as session:
        tasks = [download_and_extract_lyrics(session, idx) for idx in range(1, TOTAL + 1)]
        await asyncio.wait(tasks)


if __name__ == "__main__":
    from base import initialize_logging

    flags.DEFINE_string("download_basedir", "download/hoc5", "basedir of downloaded files")
    flags.DEFINE_string("processed_basedir", "processed/hoc5", "basedir of processed files")

    def main(_):
        initialize_logging()
        download_basepath = Path(FLAGS.download_basedir)
        download_basepath.mkdir(exist_ok=True, parents=True)
        processed_basepath = Path(FLAGS.processed_basedir)
        processed_basepath.mkdir(exist_ok=True, parents=True)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_hymns())

    app.run(main)
