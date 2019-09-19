#!/usr/bin/env python3
import os
import re
from nltk.corpus import stopwords

from tqdm import tqdm

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

def parse_doc(doc, regex_sets, stop_words):
    article_start = re.compile(r"\s*<PubmedArticle>")
    article_stop = re.compile(r"\s*</PubmedArticle>")
    pmid = re.compile(r"\s*<PMID.*>(\d*)</PMID>")
    mesh_list_start = re.compile(r"\s*<MeshHeadingList>")
    mesh_list_stop = re.compile(r"\s*</MeshHeadingList>")
    mesh_term_id = re.compile(r'\s*<DescriptorName UI="(D\d+)".*>')
    journal_start = re.compile(r"\s*<Journal>")
    journal_stop = re.compile(r"\s*</Journal>")
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
                if doc_pmid:
                    if edna.search(title) or edna.search(abstract):
                        hotwords_out = get_hotwords(regex_sets, stop_words, title, abstract)
                        term_ids = ",".join(term_ids)
                        yield (doc_pmid, journal, hotwords_out, term_ids)

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
    stop_words = set(stopwords.words("english"))
    
    organisms = []
    with open("clean_org_list", "r") as handle:
        for line in handle:
            organisms.append(re.compile(re.escape(line.strip("\n")), flags=re.IGNORECASE))

    common_names = []
    with open("org_list_common_names", "r") as handle:
        for line in handle:
            common_names.append(re.compile(re.escape(line.strip("\n")), flags=re.IGNORECASE))

    countries = []
    with open("countries", "r") as handle:
        for line in handle:
            countries.append(re.compile(re.escape(line.strip("\n")), flags=re.IGNORECASE))

    biomes = []
    with open("biomes", "r") as handle:
        for line in handle:
            biomes.append(re.compile(re.escape(line.strip("\n")), flags=re.IGNORECASE))

    tech = []
    with open("experimental_tech", "r") as handle:
        for line in handle:
            tech.append(re.compile(re.escape(line.strip("\n")), flags=re.IGNORECASE))

    sample_microenv = []
    with open("sample_types", "r") as handle:
        for line in handle:
            sample_microenv.append(re.compile(re.escape(line.strip("\n")), flags=re.IGNORECASE))
    
    hotwords = ["mammals", "fish", "amphibians", "birds", "bryophytes", "arthropods",
                    "copepods", "plants", "reptiles", "insects"]
    
    hotwords = [re.compile(re.escape(hotword), flags=re.IGNORECASE) for hotword in hotwords]

    regex_sets = [organisms, countries, biomes, tech, sample_microenv, hotwords]
    docs_list = os.listdir("/media/wkg/storage/FUSE/pubmed_bulk")
    docs_list = ["".join(["/media/wkg/storage/FUSE/pubmed_bulk/", doc]) for doc in docs_list]

    with open("relevant_metadata", "w") as out:
        for doc in tqdm(docs_list):
            for doc_metadata in parse_doc(doc, regex_sets, stop_words):
                out.write("\t".join([doc_metadata[0], doc_metadata[1], doc_metadata[2], doc_metadata[3]]))
                out.write("\n")

if __name__ == "__main__":
    main()
