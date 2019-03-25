from collections import OrderedDict

import pandas as pd
from absl import flags

import pytest
from scripture import ScriptureIndex, from_bible_cloud, from_ibibles_net, parse_locations

FLAGS = flags.FLAGS


@pytest.fixture(autouse=True)
def init():
    FLAGS(["program"])


def test_parse_locations():
    # TODO: simplify it to (chapter,verse) as it is increased in one way.
    # and then you can do search like 3:10-4:9
    r = parse_locations("撒母耳記上 17:31-49")  # 2019-02-24
    assert r == OrderedDict(
        [
            (
                "撒母耳記上17:31-49",
                ScriptureIndex(
                    book="撒母耳記上",
                    chapter=17,
                    verses=[31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
                ),
            )
        ]
    )
    r = parse_locations("哥林多前書 6:12-13;10:23-24、31")  # 2019-03-03
    assert r == OrderedDict(
        [
            ("哥林多前書6:12-13", ScriptureIndex(book="哥林多前書", chapter=6, verses=[12, 13])),
            ("哥林多前書10:23-24,31", ScriptureIndex(book="哥林多前書", chapter=10, verses=[23, 24, 31])),
        ]
    )
    r = parse_locations("約翰壹書 2:20, 24-27")  # 2019-03-10
    assert r == OrderedDict([("約翰壹書2:20,24-27", ScriptureIndex(book="約翰壹書", chapter=2, verses=[20, 24, 25, 26, 27]))])
    r = parse_locations("馬可福音 10:32-45")  # 2019-03-17
    assert r == OrderedDict(
        [
            (
                "馬可福音10:32-45",
                ScriptureIndex(
                    book="馬可福音", chapter=10, verses=[32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]
                ),
            )
        ]
    )
    r = parse_locations("馬太福音 25：14-30")  # 2019-03-24
    assert r == OrderedDict(
        [
            (
                "馬太福音25:14-30",
                ScriptureIndex(
                    book="馬太福音", chapter=25, verses=[14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
                ),
            )
        ]
    )


def test_bible_basics():
    bc = from_bible_cloud("download/CMNUNV.epub")
    bn = from_ibibles_net("download/cut/books.txt")

    assert bc.word_god == "上帝"
    assert bn.word_god == "\u3000神"

    assert len(set(bc.df.index.get_level_values(0))) == 66
    assert len(set(bn.df.index.get_level_values(0))) == 66

    df = pd.merge(bc.df, bn.df, left_index=True, right_index=True, how="outer", suffixes=("_cloud", "_net"))
    with pd.option_context(
        "display.unicode.east_asian_width", True, "display.max_colwidth", 50, "display.max_rows", 10000
    ):
        diff = df[df.isnull().any(axis=1)].copy()

        # make scripture_compare "啟示錄12:18;尼希米記13:31;歷代志上21:31;歷代志上22:19;約伯記3:3;路加福音21:30"

        # 啟示錄12:18 那時龍就站在海邊的沙上。
        # 尼希米記13:31 我又派百姓按定期獻柴和初熟的土產。我的　神啊，求你記念我，施恩與我。

        # ibibles.net all verses are misplaced.
        # 歷代志上21:31
        # 歷代志上22:19 現在你們應當立定心意，尋求耶和華－你們的神；也當起來建造耶和華　神的聖所，好將耶和華的約櫃和供奉　神的聖器皿都搬進為耶和華名建造的殿裏。」

        # 約伯記3:3 願我生的那日 和說懷了男胎的那夜都滅沒。
        # 路加福音21:30 # merged to last verse

        diff.index = diff.index.to_flat_index()
        assert diff.index.size == 6
