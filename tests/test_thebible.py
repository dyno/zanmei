from collections import OrderedDict

from absl import flags

import pytest
from thebible import BookCitations, Citation, VerseLoc, parse_citations

FLAGS = flags.FLAGS


@pytest.fixture(autouse=True)
def init():
    FLAGS(["program"])


def test_parse_citations():
    # TODO: simplify it to (chapter,verse) as it is increased in one way.
    # and then you can do search like 3:10-4:9
    r = parse_citations("撒母耳記上 17:31-49")  # 2019-02-24
    assert r == OrderedDict(
        [("撒母耳記上17:31-49", BookCitations(book="撒母耳記上", citations=[Citation(VerseLoc(17, 31), VerseLoc(17, 49))]))]
    )

    r = parse_citations("哥林多前書 6:12-13;10:23-24、31")  # 2019-03-03
    assert r == OrderedDict(
        [
            (
                "哥林多前書6:12-13",
                BookCitations(
                    book="哥林多前書",
                    citations=[Citation(start=VerseLoc(chapter=6, verse=12), end=VerseLoc(chapter=6, verse=13))],
                ),
            ),
            (
                "哥林多前書10:23-24,31",
                BookCitations(
                    book="哥林多前書",
                    citations=[
                        Citation(start=VerseLoc(chapter=10, verse=23), end=VerseLoc(chapter=10, verse=24)),
                        Citation(start=VerseLoc(chapter=10, verse=31), end=VerseLoc(chapter=10, verse=31)),
                    ],
                ),
            ),
        ]
    )
    r = parse_citations("約翰壹書 2:20, 24-27")  # 2019-03-10
    assert r == OrderedDict(
        [
            (
                "約翰壹書2:20,24-27",
                BookCitations(
                    book="約翰壹書",
                    citations=[
                        Citation(start=VerseLoc(chapter=2, verse=20), end=VerseLoc(chapter=2, verse=20)),
                        Citation(start=VerseLoc(chapter=2, verse=24), end=VerseLoc(chapter=2, verse=27)),
                    ],
                ),
            )
        ]
    )

    r = parse_citations("馬可福音 10:32-45")  # 2019-03-17
    assert r == OrderedDict(
        [
            (
                "馬可福音10:32-45",
                BookCitations(
                    book="馬可福音",
                    citations=[Citation(start=VerseLoc(chapter=10, verse=32), end=VerseLoc(chapter=10, verse=45))],
                ),
            )
        ]
    )

    r = parse_citations("馬太福音 25：14-30")  # 2019-03-24
    assert r == OrderedDict(
        [
            (
                "馬太福音25:14-30",
                BookCitations(
                    book="馬太福音",
                    citations=[Citation(start=VerseLoc(chapter=25, verse=14), end=VerseLoc(chapter=25, verse=30))],
                ),
            )
        ]
    )

    r = parse_citations("使徒行傳 4:32-5:12")
    assert r == OrderedDict(
        [
            (
                "使徒行傳4:32-5:12",
                BookCitations(
                    book="使徒行傳",
                    citations=[Citation(start=VerseLoc(chapter=4, verse=32), end=VerseLoc(chapter=5, verse=12))],
                ),
            )
        ]
    )
