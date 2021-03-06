from dataclasses import dataclass
from bs4 import BeautifulSoup
from io import StringIO
import pandas as pd
import os


@dataclass
class NanoStringSample:
    file_in: str

    def __post_init__(self):
        with open(self.file_in) as file_in:
            soup = BeautifulSoup(file_in.read(), "html.parser")
        tags = [tag.name for tag in soup.find_all()]
        for tag in tags:
            tag_string = getattr(soup, tag).string.strip()
            if tag == "code_summary":
                df = pd.read_csv(StringIO(tag_string))
                df = df[df["Name"].notnull()]
                df = df.set_index(["CodeClass", "Name", "Accession"])
                df = df.astype("float")
            else:
                df = pd.read_csv(StringIO(tag_string), names=["Attribute", "Value"])
                df = df.set_index("Attribute")
            df.columns.name = tag
            setattr(self, tag, df)
        self.ID = os.path.basename(self.file_in)
