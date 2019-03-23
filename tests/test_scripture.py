import pandas as pd
from absl import flags

import pytest
from scripture import from_bible_cloud, from_bibles_net

FLAGS = flags.FLAGS


@pytest.fixture(autouse=True)
def init():
    FLAGS(["program"])


def test_bible_basics():
    b1 = from_bible_cloud("download/CMNUNV.epub")
    b2 = from_bibles_net("download/cut/books.txt")

    assert b1.word_god == "上帝"
    assert b2.word_god == "\u3000神"

    assert len(set(b1.df.index.get_level_values(0))) == 66
    assert len(set(b2.df.index.get_level_values(0))) == 66

    df = pd.merge(b1.df, b2.df, left_index=True, right_index=True, how="outer")
    print(df[df.isnull().any(axis=1)])
