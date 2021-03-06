from dataclasses import dataclass
from typing import Any
import GEOparse
import pandas as pd
import os
import re
import numpy as np


@dataclass
class MakeHegemon:
    accessionID: str = None
    takeLog: bool = False
    export_all: bool = False

    def __post_init__(self):
        # Add GEOparse GSE object as attribute
        if self.accessionID != None:
            gse = GEOparse.get_GEO(geo=str(self.accessionID), silent=True)
            self.gse = gse

        if self.export_all:
            for _, gpl in self.gse.gpls.items():
                for method in ["expr", "idx", "survival", "ih"]:
                    func = getattr(self, method)
                    if method == "expr":
                        func = func(gpl, takeLog=self.takeLog)
                    else:
                        func = func(gpl)
                    filename = f"{self.accessionID}-{gpl.name}-{method}.txt"
                    func.to_csv(filename, sep="\t")

    def expr(self, gpl: Any, takeLog: bool) -> pd.DataFrame:
        """Pulls expression data from .soft file

        Args:
            gpl (str): a GEOparse gpl machine name
            takeLog (bool, optional): If True, function takes Log2 of all values.

        Returns:
            pandas.DataFrame: DataFrame of .soft file expression data
        """

        # if file exists, as in RNA-seq, use existing file
        expr_file = f"{self.accessionID}-{gpl.name}-expr.txt"
        if os.path.exists(expr_file):
            print("expr file exists")
            expr_df = pd.read_csv(expr_file, sep="\t")
            expr_df = expr_df.set_index(["ProbeID", "Name"])
        else:
            # confirm that gsm correlates to called gpl
            for name, gsm in self.gse.gsms.items():
                gsm_gpl = gsm.metadata["platform_id"][0]
                if gsm_gpl != gpl.name:
                    continue

                gsm_df = gsm.table.set_index("ID_REF")
                gsm_df.columns = [name]

                if takeLog:
                    # take log base two of all expr values
                    gsm_df[name] = np.where(gsm_df[name] > 0, np.log2(gsm_df[name]), -1)

                if "expr_df" not in locals():
                    expr_df = gsm_df
                else:
                    expr_df = expr_df.merge(gsm_df, left_index=True, right_index=True)
        return expr_df

    def idx(self, gpl: Any = None, expr_file: str = None) -> pd.DataFrame:
        """Makes idx dataframe including binary expression information for Boolean Network

        Args:
            gpl (str): GEO GPL name
            export (bool, optional): If True, method exports dataframe to .txt. Defaults to False.

        Returns:
            pandas.DataFrame: DataFrame including idx information
        """
        pos = 0
        idx = {
            "Ptr": [],
            "ProbeID": [],
            "Name": [],
            "Description": [],
        }

        if expr_file == None:
            expr_file = f"{self.accessionID}-{gpl.name}-expr.txt"

        with open(expr_file, "rb") as f:
            for line in f:
                if pos == 0:
                    pos += len(line)
                else:
                    idx["Ptr"].append(pos)
                    pos += len(line)
                    split = line.decode("utf-8").split("\t")
                    idx["ProbeID"].append(split[0])
                    idx["Name"].append(split[1].split(":")[0])
                    idx["Description"].append(":".join(split[1].split(":")[1:]))

        idx_df = pd.DataFrame(idx).set_index("ProbeID")

        return idx_df

    def survival(self, gpl: Any) -> pd.DataFrame:
        """Creates metadata information for each GSM (sample)

        Args:
            gpl (string): gpl name associated

        Returns:
            pd.DataFrame: survival dataframe including all samples and metadata
        """
        to_drop = [
            "geo_accession",
            "status",
            "date",
            "protocol",
            "proccesing",
            "data_processing",
            "contact",
            "supplementary",
            "platform_id",
            "series_id",
            "relation",
        ]

        all_metadata = {}
        for name, gsm in self.gse.gsms.items():
            # confirm gsm is associated with input gpl
            gsm_gpl = gsm.metadata["platform_id"][0]
            if gsm_gpl != gpl.name:
                continue

            # remove keys from metadata that aren't desired in survival
            metadata = gsm.metadata.copy()
            for key in gsm.metadata:
                for drop in to_drop:
                    if re.search(drop, key):
                        metadata.pop(key, None)
            all_metadata[name] = metadata

        all_metadata = pd.DataFrame(all_metadata).T
        # convert all list values into string
        all_metadata = all_metadata.applymap(lambda x: "\t".join(x), na_action="ignore")

        for column in all_metadata.columns:
            # split columns with multiple values into seperate columns
            to_merge = all_metadata[column].str.split("\t", expand=True)
            if len(to_merge.columns) > 1:
                # create column names for additional columns
                col_names = [str(i + 1) for i in range(len(to_merge.columns))]
                col_names = [column + "_" + name for name in col_names]
                to_merge.columns = col_names
            else:
                to_merge.columns = [column]

            if "df" not in locals():
                df = to_merge
            else:
                df = df.merge(to_merge, left_index=True, right_index=True)

        df.index.name = "ArrayID"

        for column in df.columns:
            # rename columns with cell value label
            if df[column].str.contains(":").all():
                value = df[column].str.extract(r"(.*:)").iloc[0, 0][:-1]
                df = df.rename(columns={column: value})
                df[value] = df[value].str.extract(r".*: (.*)")

        # add 'c ' label for use in hegemon
        df = df.rename(columns={col: "c " + col for col in df.columns})

        return df

    def ih(self, gpl: Any) -> pd.DataFrame:
        """DataFrame maps GSM name to sample name

        Args:
            gpl (str): gpl name associated with gsm

        Returns:
            pd.DataFrame: DataFrame mapping GSM name to sample name
        """
        survival_df = self.survival(gpl).reset_index()
        ih_df = survival_df[["ArrayID", "c title"]]
        ih_df.columns = ["ArrayID", "Title"]
        ih_df.insert(1, "ArrayHeader", ih_df["ArrayID"])
        ih_df = ih_df.set_index("ArrayID")

        return ih_df

    def explore(self) -> None:
        for gpl_name, _ in self.gse.gpls.items():
            with open(f"{gpl_name}-explore.txt", "w") as file_out:
                file_out.write("[]\n")
                file_out.write("name=\n")

                names = ["expr", "index", "survival", "indexHeader", "info"]
                file_ends = ["expr", "idx", "survival", "ih", "info"]
                for name, file_end in zip(names, file_ends):
                    my_file = f"{self.accessionID}-{gpl_name}-{file_end}.txt"
                    filepath = os.path.join(os.getcwd(), my_file)
                    file_out.write(f"{name}={filepath}\n")

                file_out.write("key=\n")
                file_out.write(f"source={self.accessionID}")
