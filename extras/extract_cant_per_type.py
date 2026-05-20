import sys
import os

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import CSV_FOLDER, CSV_SEDICI


def count_types(csv_path):
    df = pd.read_csv(csv_path, usecols=["dc.type[es]"], low_memory=False)
    counts = (
        df["dc.type[es]"]
        .value_counts(dropna=False)
        .rename_axis("type")
        .reset_index(name="count")
    )
    counts["type"] = counts["type"].fillna("(null)")
    return counts


def print_table(counts: pd.DataFrame):
    max_type_len = max(counts["type"].str.len().max(), len("type"))
    max_cnt_len = max(len(str(counts["count"].max())), len("count"))

    header = f"{'type':<{max_type_len}}  {'count':>{max_cnt_len}}"
    separator = "-" * len(header)
    print(separator)
    print(header)
    print(separator)
    for _, row in counts.iterrows():
        print(f"{row['type']:<{max_type_len}}  {row['count']:>{max_cnt_len}}")
    print(separator)
    print(f"{'TOTAL':<{max_type_len}}  {counts['count'].sum():>{max_cnt_len}}")
    print(separator)


if __name__ == "__main__":
    csv_path = CSV_FOLDER / CSV_SEDICI
    counts = count_types(csv_path)
    print_table(counts)
