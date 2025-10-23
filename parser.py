from typing import List, Tuple, Any
from Bio import Entrez
import xml.etree.ElementTree as ET
import re
import spacy
from loguru import logger
import requests
from collections import defaultdict


class Document:
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    VALID_PMC_ID_CHARS = {str(num) for num in range(0, 10)} | {"P", "M", "C"}

    def __init__(self, pmc_id: str, email: str):
        self.email = email
        self.raw_pmc_id = pmc_id.upper()

        # validate inputs
        self.validate()

        self.numeric_pmc_id = int(self.raw_pmc_id.removeprefix("PMC"))

        self._xml_content = self.fetch_pmc_xml()
        self._xml_paragraphs = self.xml_to_paragraphs()
        self._pmc_title = self.fetch_pmc_title()

        if self._pmc_title:
            logger.info(f"PMC Article Title {self._pmc_title}")

    def validate(self):
        self.validate_email()
        self.validate_pmc_id()

    def validate_pmc_id(self):
        if not all(char in self.VALID_PMC_ID_CHARS for char in self.raw_pmc_id):
            raise ValueError(f"Invalid characters in PMC ID: {self.raw_pmc_id}")
        if self.raw_pmc_id.startswith("PMC") and not self.raw_pmc_id[3:].isdigit():
            raise ValueError(f"PMC ID is incorrectly formatted: {self.raw_pmc_id}")
        if not self.raw_pmc_id.startswith("PMC") and not all(char.isdigit() for char in self.raw_pmc_id):
            raise ValueError(f"PMC ID is incorrectly formatted: {self.raw_pmc_id}")
        logger.info(f"PMC ID is valid! {self.raw_pmc_id}")
        return

    def validate_email(self):
        if not self.EMAIL_RE.fullmatch(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        logger.info(f"Email is valid! {self.email}")

    def fetch_pmc_xml(self) -> str:
        Entrez.email = self.email
        with Entrez.efetch(db="pmc", id=self.numeric_pmc_id, rettype="full", retmode="xml") as handle:
            raw = handle.read()

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")

        if "<error" in raw:
            logger.warning(f"PMC ID not in database: {self.numeric_pmc_id}")
        return raw

    def fetch_pmc_title(self) -> str | None:
        try:
            root = ET.fromstring(self._xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML for PMC {self.numeric_pmc_id}: {e}")
            return None

        for el in root.iter():
            if isinstance(el.tag, str) and el.tag.endswith("article-title"):
                txt = "".join(el.itertext()).strip()
                if txt:
                    return txt

        logger.warning(f"Article title not found for PMC {self.numeric_pmc_id}")
        return None

    def xml_to_paragraphs(self) -> List[str]:
        root = ET.fromstring(self._xml_content)
        paras = []
        for p in root.findall(".//body//p"):
            text = " ".join(t.strip() for t in p.itertext() if t.strip())
            if text:
                paras.append(text)
        return paras

    def __len__(self):
        return len(self._xml_paragraphs)

    def __getitem__(self, position):
        if isinstance(position, int):
            if position >= len(self._xml_paragraphs) or position < -len(self._xml_paragraphs):
                raise IndexError("Paragraph index out of range")
        return self._xml_paragraphs[position]

    def __repr__(self):
        return f"Document(pmc_id='{self.raw_pmc_id}', paragraphs={len(self)})"

    @property
    def paragraphs(self) -> List[str]:
        return self._xml_paragraphs

    @property
    def text(self) -> str:
        return " ".join(self._xml_paragraphs)

    @property
    def title(self) -> str | None:
        return self._pmc_title


class NLPAnalysis:
    NLP = spacy.load("en_ner_bc5cdr_md")
    HGNC_PATTERN = r"HGNC:\d+"
    HEADERS = {"Accept": "application/json"}

    HGNC_BASE = "https://rest.genenames.org/fetch/hgnc_id"
    MYGENE_QUERY = "https://mygene.info/v3/query"
    MYGENE_FIELDS = ["symbol", "name", "alias", "genomic_pos", "genomic_pos_hg19", "ensembl.gene"]

    def extract_genes_and_diseases(self, text: Document | List[str] | str) -> List[Tuple[str, str]]:
        """Extract genes with HGNC IDs and associated diseases from XML."""
        match text:
            case list():
                text_str = " ".join(text)
            case Document():
                text_str = text.text
            case str():
                text_str = text
            case _:
                raise TypeError(f"Incorrect type of text! {type(text)}")

        doc = self.NLP(text_str)

        results = []
        hgnc_disease_map = defaultdict(set)
        for sent in doc.sents:
            hgnc_ids = re.findall(self.HGNC_PATTERN, sent.text)
            if not hgnc_ids:
                continue
            found = {ent.text for ent in sent.ents if ent.label_ == "DISEASE"}
            for hgnc_id in hgnc_ids:
                hgnc_disease_map[hgnc_id].update(found)

        results = []
        for hgnc_id, diseases in hgnc_disease_map.items():
            if diseases:
                for d in diseases:
                    results.append((hgnc_id, d))
            else:
                results.append((hgnc_id, ""))
        return results

    def fetch_gene_metadata(self, records: List[Tuple[str, str]], timeout: int = 10) -> List[Tuple[Any]]:
        res = []
        for record in records:
            hgnc_id, disease = record
            hgnc_r = requests.get(f"{self.HGNC_BASE}/{hgnc_id}", headers=self.HEADERS, timeout=timeout)
            hgnc_data = hgnc_r.json()
            hgnc_docs = hgnc_data.get("response", {}).get("docs", [])
            params = {"q": hgnc_id, "fields": ",".join(self.MYGENE_FIELDS)}
            mygene_r = requests.get(self.MYGENE_QUERY, params=params, timeout=timeout)
            my_gene_result = mygene_r.json().get("hits", [])

            if hgnc_docs and my_gene_result:
                gene_record = hgnc_docs[0]
                symbol = gene_record.get("symbol")
                name = gene_record.get("name")
                alias_symbols = gene_record.get("alias_symbol", "")
                ensembl = gene_record.get("ensembl_gene_id")
                # parse mygene results
                mygene_record = my_gene_result[0]
                genomic_coords_hg38 = mygene_record["genomic_pos"]
                genomic_coords_hg19 = mygene_record["genomic_pos_hg19"]

                # change types
                if isinstance(alias_symbols, str):
                    alias_symbols = [alias_symbols]
                if not isinstance(genomic_coords_hg38, list):
                    genomic_coords_hg38 = [genomic_coords_hg38]
                if not isinstance(genomic_coords_hg19, list):
                    genomic_coords_hg19 = [genomic_coords_hg19]

                for assembly, coords_list in [("hg38", genomic_coords_hg38), ("hg19", genomic_coords_hg19)]:
                    for coord in coords_list:
                        chrom = coord.get("chr", "")
                        start = coord.get("start", "")
                        end = coord.get("end", "")
                        strand = coord.get("strand", "")

                        for alias in alias_symbols:
                            res.append(
                                (
                                    chrom,
                                    start,
                                    end,
                                    strand,
                                    assembly,
                                    hgnc_id,
                                    symbol,
                                    name,
                                    alias,
                                    ensembl,
                                    disease,
                                )
                            )
        return res
