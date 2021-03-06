#!/usr/bin/env python3


import argparse
import os

from src.NanoString import NanoString
from src.tar2rcc import tar2rcc, gunzip

__author__ = "Oliver Tucher"

parser = argparse.ArgumentParser(description="CLI For NanoString RCC Processing")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    "-d",
    "--directories",
    nargs="+",
    help="Directories of RCC files to be parsed",
)
group.add_argument(
    "-t",
    "--tarfile",
    metavar="NanoString Tarfile",
    help="NanoString Tarfile to extract (gunzip if required)",
)
parser.add_argument(
    "-o",
    "--output_dir",
    metavar="Output Directory",
    help="Directory location to file parsed data",
)

args = parser.parse_args()

if args.output_dir != None:
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    os.chdir(output_dir)
else:
    output_dir = os.getcwd()
    output_print = os.path.basename(output_dir)

if args.tarfile != None:
    rcc_dir = tar2rcc(args.tarfile)
    gunzip(rcc_dir)
    rcc_dir_list = [rcc_dir]
    NanoString(rcc_dir_list).export_all()
elif args.directories != None:
    NanoString(args.directories).export_all()

print(f"NanoString files created in: {output_print}")
