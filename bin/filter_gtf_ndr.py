#! /usr/bin/env python3 
from typing import Set
from GTF import GTF


def parse_bambu(line):
    return tuple(line)


def parse_tfkmers(line):
    ids = line[0].split("::")
    return ids[1], ids[0], line[1]


def parse_ndr(csv, origin, th) -> Set[str]:
    s = set()

    # Skip header
    next(csv)

    for line in csv:
        line = line.split(",")

        if origin == "bambu":
            line = parse_bambu(line)
        elif origin == "tfkmers":
            line = parse_tfkmers(line)

        tx_id, _, ndr = line
        ndr = float(ndr)

        if ndr < th:
            s.add(tx_id.lower())

    return s


def filter_count_matrix(file, transcripts, wr):
    print(next(file), file=wr)
    for line in file:
        line_splitted = line.split("\t")
        if line_splitted[0].startswith("BambuTx") and line_splitted[0].lower() not in transcripts:
            continue
        print(line.rstrip(), file=wr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Filter your extended GTF generated by ANNEXA. See https://github.com/igdrion/annexa for more informations"
    )

    # Required args
    parser.add_argument(
        "--gtf",
        help="Path to extended_annotations.gtf generated by ANNEXA",
        type=argparse.FileType("r"),
        required=True,
    )
    parser.add_argument(
        "--counts_tx",
        help="Path to counts_transcript.txt generated by bambu",
        type=argparse.FileType("r"),
        required=True,
    )
    parser.add_argument(
        "--bambu",
        help="Path to NDR generated by ANNEXA/bambu",
        type=argparse.FileType("r"),
        required=True,
    )
    parser.add_argument(
        "--bambu-threshold",
        help="Threshold to bambu NDR",
        type=float,
        default=0.2,
    )
    parser.add_argument(
        "--tfkmers",
        help="Path to output.csv generated by ANNEXA/transforkmers",
        type=argparse.FileType("r"),
        required=True,
    )
    parser.add_argument(
        "--tfkmers-threshold",
        help="Threshold to transforkmers NDR",
        type=float,
        default=0.2,
    )

    parser.add_argument(
        "--operation",
        help="Operation performed. Choices: union, intersection",
        type=str,
        default="intersection",
        choices=["union", "intersection"],
    )
    args = parser.parse_args()

    ###################################################
    filter_bambu = parse_ndr(args.bambu, "bambu", args.bambu_threshold)
    filter_tfkmers = parse_ndr(args.tfkmers, "tfkmers", args.tfkmers_threshold)

    if args.operation == "union":
        filter = filter_bambu | filter_tfkmers
    else:
        filter = filter_bambu & filter_tfkmers

    with open("unformat.novel.filter.gtf", "w") as wr:
        for record in GTF.parse_by_line(args.gtf):
            if "transcript_id" in record and record["transcript_id"].lower() in filter:
                print(record, file=wr)

    with open("counts_transcript.filter.txt", "w") as wr:
        filter_count_matrix(args.counts_tx, filter, wr)
