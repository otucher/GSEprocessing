#!/usr/bin/env python3

import argparse
import os

from src.MakeHegemon import MakeHegemon
from src.GetExplore import GetExplore

__author__ = "Oliver Tucher"

parser = argparse.ArgumentParser(description="CLI to make '-idx.txt' file file")
parser.add_argument(
    "expr",
    type=str,
    help="Expression file to parse",
)
parser.add_argument(
    "-o",
    "--output_dir",
    default=None,
    metavar="Output Directory",
    help="Directory location to file parsed data",
)
args = parser.parse_args()


def make_idx(expr_file: str, output_dir: str) -> None:
    """Create a '-idx.txt' file from an '-expr.txt' file

    Args:
        expr_file (str): expression file to parse
        output_dir (str, optional): directory to file output. Defaults to None.
    """
    if output_dir != None:
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        os.chdir(output_dir)

    idx_file = MakeHegemon().idx(expr_file=expr_file)
    idx_export = expr_file[:-9] + "-idx.txt"
    idx_file.to_csv(idx_export, sep="\t")

    print(f"{idx_export} file created.")

    GetExplore(expr_file)

    print(f"Explore.txt file created.")


make_idx(args.expr, output_dir=args.output_dir)
