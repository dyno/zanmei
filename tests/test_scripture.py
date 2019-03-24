import pandas as pd
from absl import flags

import pytest
from scripture import from_bible_cloud, from_bibles_net

FLAGS = flags.FLAGS


@pytest.fixture(autouse=True)
def init():
    FLAGS(["program"])


def test_bible_basics():
    bc = from_bible_cloud("download/CMNUNV.epub")
    bn = from_bibles_net("download/cut/books.txt")

    assert bc.word_god == "上帝"
    assert bn.word_god == "\u3000神"

    assert len(set(bc.df.index.get_level_values(0))) == 66
    assert len(set(bn.df.index.get_level_values(0))) == 66
    
    df = pd.merge(bc.df, bn.df, left_index=True, right_index=True, how="outer")
    with pd.option_context(
        "display.unicode.east_asian_width", True, "display.max_colwidth", 200, "display.max_rows", 10000
    ):
        print(df[df.isnull().any(axis=1) & ~df.isnull().all(axis=1)])
