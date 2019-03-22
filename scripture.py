#!/usr/bin/env python3

from functools import lru_cache
from pathlib import Path

import pandas as pd
from absl import app, flags, logging as log

flags.DEFINE_string(
    "bible_source", "download/cut/books.txt", "bible source downloaded from http://download.ibibles.net/cut.zip"
)
FLAGS = flags.FLAGS


def to_record(f):
    for line in f:
        if line.startswith(("=", "END")):
            continue
        try:
            parts = line.split(maxsplit=4)
            book = parts[2]
            chapter, verse = parts[3].split(":")
            yield (book, chapter, verse, parts[-1])
        except Exception as e:
            log.exception(f"exception processing line: {line}")


@lru_cache()
def scripture(source=None):
    if source is None:
        source = FLAGS.bible_source
    with Path(source).open() as f:
        next(f)  # get rid of the first line
        g = to_record(f)
        return pd.DataFrame.from_records(g, columns=["book", "chapter", "verse", "scripture"]).set_index(
            ["book", "chapter", "verse"]
        )


def main(argv):
    del argv
    df = scripture()
    print(df.loc[("約翰福音", "3", "16")]["scripture"])


if __name__ == "__main__":
    app.run(main)
