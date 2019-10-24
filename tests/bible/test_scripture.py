import pandas as pd
import pytest
from absl import flags

from bible.index import parse_citations
from bible.scripture import from_bible_cloud, from_ibibles_net

FLAGS = flags.FLAGS


@pytest.fixture(autouse=True)
def init():
    FLAGS(["program"])


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

        # make scripture_compare VERSES="啟示錄12:18;尼希米記13:31;歷代志上21:31;歷代志上22:19;約伯記3:3;路加福音21:30"

        # 啟示錄12:18 那時龍就站在海邊的沙上。
        # 尼希米記13:31 我又派百姓按定期獻柴和初熟的土產。我的　神啊，求你記念我，施恩與我。

        # ibibles.net all verses are misplaced.
        # 歷代志上21:31
        # 歷代志上22:19 現在你們應當立定心意，尋求耶和華－你們的神；也當起來建造耶和華　神的聖所，好將耶和華的約櫃和供奉　神的聖器皿都搬進為耶和華名建造的殿裏。」

        # 約伯記3:3 願我生的那日 和說懷了男胎的那夜都滅沒。
        # 路加福音21:30 # merged to last verse

        diff.index = diff.index.to_flat_index()
        assert diff.index.size == 6


def test_bible_search():
    bc = from_bible_cloud("download/CMNUNV.epub")
    result = bc.search(parse_citations("利未記23:10-11,15-17").items())
    verses = result["利未記23:10-11,15-17"]

    assert len(result) == 1
    assert len(verses) == 5
