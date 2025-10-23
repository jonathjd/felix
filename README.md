# Felix Overview
This program takes in a PMC ID in the format `PMC#######`, an email, and an output file path and does the following.

1. Validates that the PMC ID and email are correctly formatted.
2. Uses Biopython to fetch the PMC article XML.
2. Parses the XML and stores the title and text in the Document object.
4. Downloads the SciSpacy [en_ner_bc5cdr_md](https://allenai.github.io/scispacy/) NLP model and performs Named Entity Recognition (NER) on sentences with an HGNC ID to find the disease it is associated with.
5. Saves the HGNC ID and its associated disease(s).
6. Fetches gene metadata from [genenames](https://mygene.info/) and HGNC rest [API](https://www.genenames.org/help/rest/)
7. Saves metadata in a tab-separated file.

**Example head of saved file**:

| chrom | start      | end        | strand | assembly | hgnc_id    | symbol | name                         | alias | ensembl         | disease        |
|-------|------------|------------|--------|----------|------------|--------|------------------------------|-------|-----------------|----------------|
| 2     | 227164624  | 227314792  | 1      | hg38     | HGNC:2204  | COL4A3 | collagen type IV alpha 3 chain |       | ENSG00000169031 | MIM 203780     |
| 2     | 228029281  | 228179508  | 1      | hg19     | HGNC:2204  | COL4A3 | collagen type IV alpha 3 chain |       | ENSG00000169031 | MIM 203780     |
| 22    | 36253071   | 36267530   | 1      | hg38     | HGNC:618   | APOL1  | apolipoprotein L1            |       | ENSG00000100342 | kidney disease |
| 22    | 36649056   | 36663576   | 1      | hg19     | HGNC:618   | APOL1  | apolipoprotein L1            |       | ENSG00000100342 | kidney disease |

### File fields and types:
- **chrom**: STRING - Chromosome number/identifier
- **start**: INTEGER - Genomic start position 
- **end**: INTEGER - Genomic end position
- **strand**: INTEGER - Strand orientation (1 for forward, -1 for reverse)
- **assembly**: STRING - Genome assembly version (hg38/hg19)
- **hgnc_id**: STRING - HGNC identifier in format "HGNC:#####"
- **symbol**: STRING - Official HGNC gene symbol
- **name**: STRING - Full gene name/description
- **alias**: STRING - Alternative gene name/symbol
- **ensembl**: STRING - Ensembl gene identifier
- **disease**: STRING - Associated disease

## How to Run
Requires Python 3.11+.
1. Clone the repo
```bash
git clone https://github.com/jonathjd/felix.git && cd felix
```

2. Make a virtual environment and install dependencies.
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

if using `uv`

```bash
uv sync
```

3. Run the program
Use the following command, replacing the arguments as needed:

```bash
python main.py --pmc_id PMC####### --email your.email@domain.com --output genes.tsv
```

- `--pmc_id` or `-pid`: The PMC article ID (e.g. PMC11123321)
- `--email` or `-e`: Your email address (required by NCBI)
- `--output` or `-o`: Output TSV file path
