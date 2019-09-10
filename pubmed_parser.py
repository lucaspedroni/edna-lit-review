#!/usr/bin/env python3
import os
import re
from tqdm import tqdm

def get_hotwords(hotwords, title, abstract):
    # clean up data
    chars = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    
    text = " ".join([title, abstract])
    text = text.split()

    clean_words = []
    for word in text:
        word_out = "".join([letter for letter in word if letter in chars])
        clean_words.append(word_out)

    clean_words = " ".join(clean_words)

    hotwords_out = []
    for hotword in hotwords:
        if hotword in clean_words:
            hotwords_out.append(hotword)

    return hotwords_out


def parse_doc(doc, hotwords):
    article_start = re.compile(r"\s*<PubmedArticle>")
    article_stop = re.compile(r"\s*</PubmedArticle>")
    pmid = re.compile(r"\s*<PMID.*>(\d*)</PMID>")
    mesh_list_start = re.compile(r"\s*<MeshHeadingList>")
    mesh_list_stop = re.compile(r"\s*</MeshHeadingList>")
    mesh_term_id = re.compile(r'\s*<DescriptorName UI="(D\d+)".*>')
    journal_start = re.compile(r"\s*<Journal>")
    journal_stop = re.compile(r"\s*</Journal")
    journal_name = re.compile(r"\s*<Title>(.+)</Title")
    article_title = re.compile(r"\s*<ArticleTitle>(.+)</ArticleTitle")
    abstract_start = re.compile(r"\s*<Abstract>")
    abstract_stop = re.compile(r"\s*</Abstract>")
    abstract_text = re.compile(r"\s*<AbstractText.*>(.*)</AbstractText")
    edna = re.compile(r"[Ee]nvironmental DNA")

    doc_pmid = ""
    abstract = ""
    title = ""
    journal = ""
    term_ids = []

    with open(doc, "r") as handle:
        line = handle.readline()
        while line:
            if article_start.search(line):
                if doc_pmid and title and abstract:
                    if edna.search(title) or edna.search(abstract):
                        hotwords_out = get_hotwords(hotwords, title, abstract)
                        yield (doc_pmid, journal, hotwords_out)
                    # reset vars
                    doc_pmid = ""
                    journal = ""
                    abstract = ""
                    title = ""
                    term_ids = []

                while not article_stop.search(line):
                    if not doc_pmid and pmid.search(line):
                        doc_pmid = pmid.search(line).group(1)
                    if mesh_list_start.search(line):
                        while not mesh_list_stop.search(line):
                            mesh_match = mesh_term_id.search(line)
                            if mesh_match and mesh_match.group(1):
                                term_ids.append(mesh_match.group(1))
                            line = handle.readline()
                    if journal_start.search(line):
                        while not journal_stop.search(line):
                            journal_match = journal_name.search(line)
                            if journal_match and journal_match.group(1):
                                journal = journal_match.group(1)
                            line = handle.readline()
                    if article_title.search(line):
                        title = article_title.search(line).group(1)
                    if abstract_start.search(line):
                        abs_lines = []
                        while not abstract_stop.search(line):
                            abs_match = abstract_text.search(line)
                            if abs_match and abs_match.group(1):
                                abs_lines.append(abs_match.group(1))
                            line = handle.readline()
                        abstract = " ".join(abs_lines)
                        
                    line = handle.readline()
            line = handle.readline()

def main():
    hotwords = []
    with open("clean_org_list", "r") as handle:
        for line in handle:
            line = line.strip("\n")
            hotwords.append(line)
    hotwords.extend(["soil", "16S", "18S", "metabarcoding", "barcoding", "COI",
                    "sediment", "saltwater", "freshwater", "ice", "glacial",
                    "floodplain"])
    hotwords = set(hotwords)

    docs_list = os.listdir("/media/wkg/storage/FUSE/pubmed_bulk")
    docs_list = ["".join(["/media/wkg/storage/FUSE/pubmed_bulk/", doc]) for doc in docs_list]

    with open("relevant_metadata", "w") as out:
        for doc in tqdm(docs_list[:200]):
            for doc_metadata in parse_doc(doc, hotwords):
                doc_hotwords = ",".join(doc_metadata[2])
                out.write("\t".join([doc_metadata[0], doc_metadata[1], doc_hotwords]))
                out.write("\n")

if __name__ == "__main__":
    main()