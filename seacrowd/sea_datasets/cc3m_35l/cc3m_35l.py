import os
from typing import Dict, List, Tuple

import datasets
import json
import pandas as pd

from seacrowd.utils import schemas
from seacrowd.utils.configs import SEACrowdConfig
from seacrowd.utils.constants import Licenses, Tasks


_CITATION = """\
@inproceedings{thapliyal-etal-2022-crossmodal,
    title = "Crossmodal-3600: A Massively Multilingual Multimodal Evaluation Dataset",
    author = "Thapliyal, Ashish V.  and
      Pont Tuset, Jordi  and
      Chen, Xi  and
      Soricut, Radu",
    editor = "Goldberg, Yoav  and
      Kozareva, Zornitsa  and
      Zhang, Yue",
    booktitle = "Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing",
    month = dec,
    year = "2022",
    address = "Abu Dhabi, United Arab Emirates",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2022.emnlp-main.45",
    doi = "10.18653/v1/2022.emnlp-main.45",
    pages = "715--729",
}
"""

_DATASETNAME = "cc3m_35l"

_DESCRIPTION = """\
    CC3M-35L is created by translating Conceptual Captions 3M (Sharma et al., 2018),
    originally in English, to the other 34 languages using Google's machine translation API.
"""

_HOMEPAGE = "https://google.github.io/crossmodal-3600/"

_LICENSE = Licenses.CC_BY_4_0.value

# the image URLs are contained in tsv file together with the original captions which can be downloaded locally using google account.
# those tsv file originally can be found and downloaded from this page https://ai.google.com/research/ConceptualCaptions/download
# there are no direct image folder ready, so it needs to be downloaded one by one
# some warnings may occur when downloading due to reasons such as security certificate and others
_URLS = {
    "trans_train": "https://storage.googleapis.com/crossmodal-3600/cc3m_mt_train.jsonl.bz2",
    "trans_dev": "https://storage.googleapis.com/crossmodal-3600/cc3m_mt_dev.jsonl.bz2",
}

_SUPPORTED_TASKS = [Tasks.IMAGE_CAPTIONING]

_SOURCE_VERSION = "1.0.0"

_SEACROWD_VERSION = "2024.06.20"

_LANGUAGES = ["fil", "ind", "tha", "vie"]

LANGUAGE_MAP = {
    'fil': 'fil',
    'ind': 'id',
    'tha': 'th',
    'vie': 'vi',
}

class CC3M35L(datasets.GeneratorBasedBuilder):
    """
    CC3M-35L is created by translating Conceptual Captions 3M (Sharma et al., 2018),
    originally in English, to the other 34 languages using Google's machine translation API.
    """

    SOURCE_VERSION = datasets.Version(_SOURCE_VERSION)
    SEACROWD_VERSION = datasets.Version(_SEACROWD_VERSION)

    BUILDER_CONFIGS = [
        SEACrowdConfig(name=f"cc3m_35l_{lang}_source", version=datasets.Version(_SOURCE_VERSION), description=f"cc3m_35l_{lang} source schema", schema="source", subset_id=f"cc3m_35l_{lang}",)
        for lang in _LANGUAGES
    ] + [
        SEACrowdConfig(
            name=f"{_DATASETNAME}_{lang}_seacrowd_imtext",
            version=datasets.Version(_SEACROWD_VERSION),
            description=f"{_DATASETNAME}_{lang} SEACrowd schema",
            schema="seacrowd_imtext",
            subset_id=f"{_DATASETNAME}_{lang}",
        )
        for lang in _LANGUAGES
    ]


    DEFAULT_CONFIG_NAME = "cc3m_35l_id_source"

    def _info(self) -> datasets.DatasetInfo:
        if self.config.schema == "source":
            features = datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "image_paths": datasets.Value("string"),
                    "src_lang": datasets.Value("string"),
                    "caption_tokenized": datasets.Value("string"),
                    "trg_lang": datasets.Value("string"),
                    "translation_tokenized": datasets.Value("string"),
                    "backtranslation_tokenized": datasets.Value("string"),
                }
            )
        elif self.config.schema == "seacrowd_imtext":
            features = schemas.image_text_features()

        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def fill_img_path(self, df: pd.DataFrame, line: dict):
        exceptions = []
        selected_row = df.query('caption==@line["caption_tokenized"]')
        # it may return several rows, skip of empty
        if not selected_row.empty:
            # for each row, download the image, use its path and put the translation
            for idx, row in selected_row.iterrows():
                row["trans_caption"] = line["translation_tokenized"]
                row["backtrans_caption"] = line["backtranslation_tokenized"]
                # if the image cannot be downloaded for some reason, skip it
                # may cause difference in the total data each run
                try:
                    row["img_path"] = datasets.DownloadManager().download(row["img_url"])
                except:
                    exceptions.append(idx)

        return selected_row, exceptions

    def is_target(self, line: dict, trg_lang: str):
        if line["trg_lang"] == trg_lang:
            return line

    def _split_generators(self, dl_manager: datasets.DownloadManager) -> List[datasets.SplitGenerator]:
        """Returns SplitGenerators."""
        dev_path = dl_manager.download_and_extract(_URLS["trans_dev"])
        train_path = dl_manager.download_and_extract(_URLS["trans_train"])
        current_lang = LANGUAGE_MAP[self.config.subset_id.split("_")[2]]
        if self.config.data_dir is None:
            raise ValueError("This is a local dataset. Please pass the data_dir kwarg to load_dataset.")
        else:
            data_dir = self.config.data_dir

        ###
        # Dev Data
        ###
        dev_handler = open(dev_path, 'r')
        gcc_val_df = pd.read_csv(os.path.join(data_dir, 'Validation_GCC-1.1.0-Validation.tsv'), sep="\t", header=None, names=["caption", "img_url"])
        gcc_val_df.index = gcc_val_df.index + 1
        
        ###
        # Train Data
        ###
        trn_handler = open(train_path, 'r')
        gcc_trn_df = pd.read_csv(os.path.join(data_dir, 'Train_GCC-training.tsv'), sep="\t", header=None, names=["caption", "img_url"])
        gcc_trn_df.index = gcc_trn_df.index + 1

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={
                    "data": (trn_handler, gcc_trn_df),
                    "lang": current_lang,
                    "split": "train",
                },
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION,
                gen_kwargs={
                    "data": (dev_handler, gcc_val_df),
                    "lang": current_lang,
                    "split": "dev",
                },
            ),
        ]

    def _generate_examples(self, data: tuple, lang: str, split: str) -> Tuple[int, Dict]:
        """Yields examples as (key, example) tuples."""
        split_handler, gcc_df = data
        
        idx, c_data = -1, None
        while True:
            line = split_handler.readline().strip()
            if not line:
                split_handler.seek(0)
                return idx, c_data # Return last data            
                
            # Matching index
            row = json.loads(line)
            if row['trg_lang'] != lang:
                continue
                
            index = row['rec_num']
            caption = row['caption_tokenized']
            img_url = gcc_df.loc[index,'img_url']
            
            if c_data is not None:
                yield idx, c_data
            
            idx += 1
            if self.config.schema == "source":
                c_data = {
                    "id": str(idx),
                    "image_paths": img_url,
                    "src_lang": "en",
                    "caption_tokenized": caption,
                    "trg_lang": self.config.subset_id.split("_")[2],
                    "translation_tokenized": row["translation_tokenized"],
                    "backtranslation_tokenized": row["backtranslation_tokenized"],
                }

            elif self.config.schema == "seacrowd_imtext":
                c_data = {
                    "id": str(idx),
                    "image_paths": [img_url],
                    "texts": row["translation_tokenized"],
                    "metadata": {
                        "context": None,
                        "labels": None,
                    },
                }
            else:
                raise ValueError(f"Invalid config: {self.config.name}")