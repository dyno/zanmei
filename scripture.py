#!/usr/bin/env python3
import re
import warnings
from collections import OrderedDict, namedtuple
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pandas as pd
from absl import app, flags, logging as log

flags.DEFINE_string("bible_source", "download/cut/books.txt", "books.txt from http://download.ibibles.net/cut.zip")
flags.DEFINE_string("bible_index", "約翰福音3:16;14:6", "bible search by location")

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
    # https://stackoverflow.com/questions/17912307/u-ufeff-in-python-string
    with Path(source).open(encoding="utf-8-sig") as f:
        df = pd.DataFrame.from_records(to_record(f), columns=["book", "chapter", "verse", "scripture"])
        df.set_index(["book", "chapter", "verse"], inplace=True)
        # if 2 verses merged to 1, use the 1st verse and clear the 2nd.
        warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
        df["scripture"] = df["scripture"].str.strip().str.replace("。", "。")
        df.loc[df["scripture"].str.startswith("見上節"), ["scripture"]] = ""

        return df


ScriptureIndex = namedtuple("ScriptureIndex", ["book", "chapter", "verses"])


def parse_locations(locations: str) -> Dict[str, ScriptureIndex]:
    """
    >>> from pprint import pprint
    >>> pprint(parse_locations("撒母耳記上 17:31-49")) # 2019-02-24 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('撒母耳記上17:31-49',
              ScriptureIndex(book='撒母耳記上', chapter='17', verses=['31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49']))])
    >>> pprint(parse_locations("哥林多前書 6:12-13;10:23-24、31")) # 2019-03-03 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('哥林多前書6:12-13',
              ScriptureIndex(book='哥林多前書', chapter='6', verses=['12', '13'])),
             ('哥林多前書10:23-24,31',
              ScriptureIndex(book='哥林多前書', chapter='10', verses=['23', '24', '31']))])
    >>> pprint(parse_locations("約翰壹書 2:20, 24-27")) # 2019-03-10 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('約翰壹書2:20,24-27',
              ScriptureIndex(book='約翰壹書', chapter='2', verses=['20', '24', '25', '26', '27']))])
    >>> pprint(parse_locations("馬可福音 10:32-45")) # 2019-03-17 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('馬可福音10:32-45',
              ScriptureIndex(book='馬可福音', chapter='10', verses=['32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45']))])
    >>> pprint(parse_locations("馬太福音 25：14-30")) # 2019-03-24 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('馬太福音25:14-30',
              ScriptureIndex(book='馬太福音', chapter='25', verses=['14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30']))])
    """
    result = OrderedDict()

    loc_list = re.split(r"[;；]", locations)
    prev_book = None
    for loc in loc_list:
        # normalize location <book>chapter:verse-verse,verse;chapter:verse
        loc = (
            loc.replace("～", "-")
            .replace("－", "-")
            .replace("，", ",")
            .replace("、", ",")
            .replace("：", ":")
            .replace("　", "")
            .replace(" ", "")
        )

        # 1. book
        # use 約翰一書 not 約翰1書
        m = re.search(r"^(?P<book>[^0-9 ]+)\s*", loc)
        if m:
            book = m.group("book")
            prev_book = book
            chapter_verses = loc[len(book) :]
        else:
            assert prev_book is not None
            book = prev_book
            chapter_verses = loc
            loc = book + chapter_verses

        # 2. chapter
        # 11:12-15,19
        parts = chapter_verses.strip().split(":")
        chapter = parts[0]
        ranges = parts[1]

        # 3. verses
        verses = []
        for r in ranges.split(","):
            parts = r.split("-")
            if len(parts) == 1:
                verses.append(parts[0])
            else:
                l, r = map(int, parts)
                verses.extend([str(i) for i in range(l, r + 1)])

        result[loc] = ScriptureIndex(book, chapter, verses)

    return result


def search(bible: pd.DataFrame, locations: str) -> Dict[str, List[str]]:
    loc_list = parse_locations(locations)
    result = OrderedDict()
    for loc, scripture_index in loc_list.items():
        df = bible.loc[scripture_index]
        result[loc] = df

    return result


def main(argv):
    del argv
    bible = scripture()
    with pd.option_context("display.unicode.east_asian_width", True, "display.max_colwidth", 200):
        result = search(bible, FLAGS.bible_index)
        for loc, verses in result.items():
            print(loc)
            for t in verses.itertuples():
                print(f"{t.Index[-1]:>3s} {t.scripture}")
            print()


if __name__ == "__main__":
    app.run(main)
