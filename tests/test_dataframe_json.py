import pandas as pd
import pytest

from src.adapters.api.dataframe_json import dataframe_from_split_json, dataframe_to_split_json


def test_dataframe_split_json_roundtrip():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})

    df_json = dataframe_to_split_json(df)
    restored = dataframe_from_split_json(df_json)

    pd.testing.assert_frame_equal(restored, df)


def test_dataframe_split_json_missing_payload():
    with pytest.raises(ValueError, match="Missing df_json payload"):
        dataframe_from_split_json("")
