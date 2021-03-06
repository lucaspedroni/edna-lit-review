#!/usr/bin/env python3
import os
import re
import time
import logging
from pathlib import Path

from nltk.corpus import stopwords
from tqdm import tqdm

global logger

def get_hotwords(regex_sets, stop_words, title, abstract):
    # clean up data
    chars = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    
    text = " ".join([title, abstract])
    text = text.split()
    
    clean_words = []
    for word in text:
        word_out = "".join([letter for letter in word if letter in chars])
        word_out = word_out.lower()
        if word_out not in stop_words:
            clean_words.append(word_out)

    clean_words = " ".join(clean_words)

    out = []
    for regex_set in regex_sets:
        regex_hits = []
        for regex in regex_set:
            if regex.search(clean_words):
                regex_hits.append(regex.search(clean_words).group())
        regex_hits = ",".join(regex_hits)
        out.append(regex_hits)

    return "\t".join(out)

def parse_doc(doc, regex_sets, stop_words, doc_totals, logger):
    article_start = re.compile(r"\s*<PubmedArticle>")
    article_stop = re.compile(r"\s*</PubmedArticle>")
    pmid = re.compile(r"\s*<PMID.*>(\d*)</PMID>")
    mesh_list_start = re.compile(r"\s*<MeshHeadingList>")
    mesh_list_stop = re.compile(r"\s*</MeshHeadingList>")
    mesh_term_id = re.compile(r'\s*<DescriptorName UI="(D\d+)".*>')
    journal_start = re.compile(r"\s*<Journal>")
    journal_stop = re.compile(r"\s*</Journal>")
    journal_name = re.compile(r"\s*<Title>(.+)</Title")
    pub_year = re.compile(r"\s*<Year>(\d+)</Year>")
    article_title = re.compile(r"\s*<ArticleTitle>(.+)</ArticleTitle")
    abstract_start = re.compile(r"\s*<Abstract>")
    abstract_stop = re.compile(r"\s*</Abstract>")
    abstract_text = re.compile(r"\s*<AbstractText.*>(.*)</AbstractText")
    #edna = re.compile(r"([Ee]nvironmental DNA)|(DNA barcod)")
#    edna = re.compile(r"[Ee]nvironmental DNA")
#    barcode = re.compile(r"DNA barcod")

    barcode_mesh_id = "D058893"

    doc_pmid = ""
    abstract = ""
    title = ""
    journal = ""
    term_ids = []
    year = ""

    doc_count = 0
    
    start_time = time.perf_counter()
    with open(doc, "r") as handle:
        line = handle.readline()
        while line:
            if article_start.search(line):
                doc_count += 1
                if doc_pmid:
                    #if edna.search(title) or edna.search(abstract) or barcode_mesh_id in term_ids:
                    if barcode_mesh_id in term_ids:
                        hotwords_out = get_hotwords(regex_sets, stop_words, title, abstract)
                        term_ids = ",".join(term_ids)
                        yield (doc_pmid, journal, year, hotwords_out, term_ids)

                    # reset vars
                    doc_pmid = ""
                    journal = ""
                    abstract = ""
                    title = ""
                    term_ids = []
                    year = ""

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
                            year_match = pub_year.search(line)
                            if year_match and year_match.group(1):
                                year = year_match.group(1)
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
    
    elapsed_time = int((time.perf_counter() - start_time) * 10) / 10.0
    logger.info(f"parsed: |{doc_count}| articles in {elapsed_time} seconds")
    doc_totals.append(doc_count)

def main():
    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("pubmed_parser_uids.log")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    doc_totals = []

    stop_words = set(stopwords.words("english"))
    
    organisms = []
    with open("clean_org_list", "r") as handle:
        for line in handle:
            item = "".join([r"\b", re.escape(line.strip("\n")), r"\b"])
            organisms.append(re.compile(item, flags=re.IGNORECASE))

    common_names = []
    with open("org_list_common_names", "r") as handle:
        for line in handle:
            item = "".join([r"\b", re.escape(line.strip("\n")), r"\b"])
            common_names.append(re.compile(item, flags=re.IGNORECASE))

    countries = []
    with open("countries", "r") as handle:
        for line in handle:
            item = "".join([r"\b", re.escape(line.strip("\n")), r"\b"])
            countries.append(re.compile(item, flags=re.IGNORECASE))

    biomes = []
    with open("biomes", "r") as handle:
        for line in handle:
            item = "".join([r"\b", re.escape(line.strip("\n")), r"\b"])
            biomes.append(re.compile(item, flags=re.IGNORECASE))

    tech = []
    with open("experimental_tech", "r") as handle:
        for line in handle:
            item = "".join([r"\b", re.escape(line.strip("\n")), r"\b"])
            tech.append(re.compile(item, flags=re.IGNORECASE))

    sample_microenv = []
    with open("sample_types", "r") as handle:
        for line in handle:
            item = "".join([r"\b", re.escape(line.strip("\n")), r"\b"])
            sample_microenv.append(re.compile(item, flags=re.IGNORECASE))
    
    hotwords = ["mammals", "fish", "amphibians", "birds", "bryophytes", "arthropods",
                    "copepods", "plants", "reptiles", "insects"]
    
    hotwords = [re.compile(re.escape(hotword), flags=re.IGNORECASE) for hotword in hotwords]

    regex_sets = [organisms, common_names, countries, biomes, tech, sample_microenv, hotwords]

    doc_dir = "/media/wkg/storage/FUSE/pubmed_bulk"
    docs_list = os.listdir(doc_dir)
    containing_dir = Path(doc_dir).resolve()
    
    docs_list = [os.path.join(containing_dir, doc) for doc in docs_list]

    with open("relevant_metadata_incl_barcoding_meshterm", "w") as out:
        for doc in tqdm(docs_list):
            for doc_metadata in parse_doc(doc, regex_sets, stop_words, doc_totals, logger):
                out.write("\t".join([doc_metadata[0], doc_metadata[1], doc_metadata[2], 
                    doc_metadata[3], doc_metadata[4]]))
                out.write("\n")

    tot = sum(doc_totals)
    logger.info(f"total articles: {tot}")

if __name__ == "__main__":
    main()
