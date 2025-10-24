import argparse
import csv
from pathlib import Path
import sys

from loguru import logger

from felix.parser import Document, NLPAnalysis
from felix.validators import validate_email, validate_pmc_id

OUTPUT_HEADER = [
    "chrom",
    "start",
    "end",
    "strand",
    "assembly",
    "hgnc_id",
    "symbol",
    "name",
    "alias",
    "ensembl",
    "disease",
]


def main():
    parser = argparse.ArgumentParser(
        description="A CLI tool to extract genes and associated metadata from publically available pubmed articles"
    )
    parser.add_argument("--pmc_id", "-pid", required=True, help="The PMC ID of the article (e.g. PMC1312717).")
    parser.add_argument("--email", "-e", required=True, help="Email for NCBI Entrez.")
    parser.add_argument("--output", "-o", help="File to write results to. Writes to stdout if omitted.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # validate inputs
    validate_pmc_id(args.pmc_id)
    validate_email(args.email)

    document = Document(args.pmc_id, args.email)
    analysis = NLPAnalysis()
    records = analysis.extract_genes_and_diseases(document)
    metadata = analysis.fetch_gene_metadata(records)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(OUTPUT_HEADER)
        writer.writerows(metadata)

    unique_hgnc_ids = {row[0] for row in metadata} if metadata else {}
    logger.info(f"{len(unique_hgnc_ids)} unique HGNC IDs found.")


if __name__ == "__main__":
    main()
