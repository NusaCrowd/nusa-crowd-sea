# coding=utf-8
# Copyright 2022 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The Madurese Parallel Corpus Dataset is created by scraping content from the online Bible, resulting in 30,013 Indonesian-Madurese sentences.
This corpus is distinct from a previous Madurese dataset, which was gathered from physical documents such as the Kamus Lengkap Bahasa Madura-Indonesia.
The proposed dataset provides bilingual sentences, allowing for comparisons between Indonesian and Madurese. It aims to supplement existing Madurese
corpora, enabling enhanced research and development focused on regional languages in Indonesia. Unlike the prior dataset that included information
like lemmas, pronunciation, linguistic descriptions, part of speech, loanwords, dialects, and various structures, this new corpus primarily focuses
on bilingual sentence pairs, potentially broadening the scope for linguistic studies and language technology advancements in the Madurese language.
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple

import datasets
import jsonlines

from seacrowd.utils import schemas
from seacrowd.utils.configs import SEACrowdConfig
from seacrowd.utils.constants import Licenses, Tasks

_CITATION = """\
@article{,
  author    = {Sulistyo, Danang Arbian and Wibawa, Aji Prasetya and Prasetya, Didik Dwi and Nafalski, Andrew},
  title     = {Autogenerated Indonesian-Madurese Parallel Corpus Dataset Using Neural Machine Translation},
  journal   = {Available at SSRN 4644430},
  volume    = {},
  year      = {2023},
  url       = {https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4644430},
  doi       = {},
  biburl    = {},
  bibsource = {}
}
"""

_DATASETNAME = "indonesian_madurese_bible_translation"

_DESCRIPTION = """\
The Madurese Parallel Corpus Dataset is created by scraping content from the online Bible, resulting in 30,013 Indonesian-Madurese sentences.
This corpus is distinct from a previous Madurese dataset, which was gathered from physical documents such as the Kamus Lengkap Bahasa Madura-Indonesia.
The proposed dataset provides bilingual sentences, allowing for comparisons between Indonesian and Madurese. It aims to supplement existing Madurese
corpora, enabling enhanced research and development focused on regional languages in Indonesia. Unlike the prior dataset that included information
like lemmas, pronunciation, linguistic descriptions, part of speech, loanwords, dialects, and various structures, this new corpus primarily focuses
on bilingual sentence pairs, potentially broadening the scope for linguistic studies and language technology advancements in the Madurese language.
"""

_HOMEPAGE = "https://data.mendeley.com/datasets/cgtg4bhrtf/3"
_LANGUAGES = ["ind", "mad"]  # We follow ISO639-3 language code (https://iso639-3.sil.org/code_tables/639/data)
_LICENSE = Licenses.CC_BY_4_0.value  # example: Licenses.MIT.value, Licenses.CC_BY_NC_SA_4_0.value, Licenses.UNLICENSE.value, Licenses.UNKNOWN.value
_LOCAL = False
_URLS = {
    _DATASETNAME: "https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/cgtg4bhrtf-3.zip",
}
_SUPPORTED_TASKS = [Tasks.MACHINE_TRANSLATION]  # example: [Tasks.TRANSLITERATION, Tasks.NAMED_ENTITY_RECOGNITION, Tasks.RELATION_EXTRACTION]
_SOURCE_VERSION = "1.0.0"
_SEACROWD_VERSION = "1.0.0"


class IndonesianMadureseBibleTranslationDataset(datasets.GeneratorBasedBuilder):
    """TODO: This corpus consists of more than 20,000 Indonesian - Madurese sentences."""

    SOURCE_VERSION = datasets.Version(_SOURCE_VERSION)
    SEACROWD_VERSION = datasets.Version(_SEACROWD_VERSION)

    BUILDER_CONFIGS = [
        SEACrowdConfig(
            name=f"{_DATASETNAME}_source",
            version=SOURCE_VERSION,
            description=f"{_DATASETNAME} source schema",
            schema="source",
            subset_id=f"{_DATASETNAME}",
        ),
        SEACrowdConfig(
            name=f"{_DATASETNAME}_seacrowd_t2t",
            version=SEACROWD_VERSION,
            description=f"{_DATASETNAME} SEACrowd schema",
            schema="seacrowd_t2t",
            subset_id=f"{_DATASETNAME}",
        ),
    ]

    DEFAULT_CONFIG_NAME = "indonesian_madurese_bible_translation_source"

    def _info(self) -> datasets.DatasetInfo:
        if self.config.schema == "source":
            features = datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "src": datasets.Value("string"),
                    "tgt": datasets.Value("string"),
                }
            )

        elif self.config.schema == "seacrowd_t2t":
            features = schemas.text2text_features

        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager: datasets.DownloadManager) -> List[datasets.SplitGenerator]:
        """Returns SplitGenerators."""

        urls = _URLS[_DATASETNAME]
        data_dir = dl_manager.download_and_extract(urls)
        data_dir = os.path.join(data_dir, "Bahasa Madura Corpus Dataset/Indonesian-Madurese Corpus")
        all_raw_path = [data_dir + "/" + item for item in os.listdir(data_dir)]
        all_path = []
        id = 0
        for raw_path in all_raw_path:
            if "txt" in raw_path:
                all_path.append(raw_path)
        all_data = []
        for path in all_path:
            data = self._read_txt(path)
            for line in data:
                if line != "\n":
                    all_data.append({"src": line.split("\t")[0], "tgt": line.split("\t")[1], "id": id})
                id += 1
        self._write_jsonl(data_dir + "/train.jsonl", all_data)

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                # Whatever you put in gen_kwargs will be passed to _generate_examples
                gen_kwargs={
                    "filepath": os.path.join(data_dir, "train.jsonl"),
                    "split": "train",
                },
            )
        ]

    def _generate_examples(self, filepath: Path, split: str) -> Tuple[int, Dict]:
        """Yields examples as (key, example) tuples."""
        if self.config.schema == "source":
            i = 0
            with jsonlines.open(filepath) as f:
                for each_data in f.iter():
                    ex = {
                        "id": each_data["id"],
                        "src": each_data["src"],
                        "tgt": each_data["tgt"],
                    }
                    yield i, ex
                    i += 1

        elif self.config.schema == "seacrowd_t2t":
            i = 0
            with jsonlines.open(filepath) as f:
                for each_data in f.iter():
                    ex = {"id": each_data["id"], "text_1": each_data["src"].strip(), "text_2": each_data["tgt"].strip(), "text_1_name": "ind", "text_2_name": "mad"}
                    yield i, ex
                    i += 1

    def _write_jsonl(self, filepath, values):
        with jsonlines.open(filepath, "w") as writer:
            for line in values:
                writer.write(line)

    def _read_txt(self, filepath):
        with open(filepath, "r") as f:
            lines = f.readlines()
        return lines
