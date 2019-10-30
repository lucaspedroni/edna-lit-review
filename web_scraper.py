#!/usr/bin/env python3
import re
import sys
import time
import logging
import traceback
import configparser
import urllib.robotparser
from urllib.parse import urlparse

import requests
import scholarly
from bs4 import BeautifulSoup

# TODO: returning disallowed for some domains that should be allowed, see logs
def robots_allowed(url, checked_netlocs, logger):
    # extract base domain
    netloc = urlparse(url).netloc

    if netloc not in checked_netlocs:
        robot_parser = urllib.robotparser.RobotFileParser()
        robot_parser.set_url(f"http://{netloc}/robots.txt")
        robot_parser.read()

        if robot_parser.can_fetch("*", url):
            checked_netlocs.append(netloc)
            return True
        else:
            logger.info(f"Disallowed from {netloc}, {url}")
            return False
    else:
        return True

def extract_natural_text(soup):
        text = [" ".join([str(it).strip() for it in item.contents]) for item in soup]
        text = [remove_tags(item) for item in text if item and item != " " 
                and not item.startswith("<a")]
        text = list(dict.fromkeys(text))
        
        # could be additional validation step here
        return " ".join([item for item in text if len(item) > 25])
        
def remove_tags(string):
    out = []
    within_tag = False
    for letter in string:
        if letter != "<" and not within_tag:
            out.append(letter)
        if letter == "<":
            within_tag = True
        if letter == ">" and within_tag:
            within_tag = False
    
    return "".join(out)

if __name__ == "__main__":   
    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("gs_webscraper.log")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Get User-Agent data
    config = configparser.ConfigParser()
    config.read("scraper.cfg")

    checked_netlocs = []

    valid_text = re.compile(r"[Ee]nvironmental|DNA")
    
    headers = requests.utils.default_headers()
    headers["User-Agent"] = config.get("scraper", "user_agent")
    
    query = scholarly.search_pubs_query("environmental DNA")
    
    # Check timing of requests
    last_req = time.perf_counter()
#    texts = []
#    authors = []
#    titles = []
#    cit_counts = []
    with open("gs_scrape_results", "w") as out:
        for query_result in query:
            try:
                if time.perf_counter() - last_req < 1:
                    time.sleep(1)

                title = query_result.bib["title"]
                author = query_result.bib["author"] 
                cit_count = query_result.citedby
                url = query_result.bib['url']

                if robots_allowed(url, checked_netlocs, logger):
                    result = requests.get(url, headers=headers)
                    
                    soup = BeautifulSoup(result.content, features="html5lib")
                    text = extract_natural_text(soup.find_all("p"))
                    
                    # more validation here:
                    if valid_text.search(text):
                        out.write("\t".join([author, title, str(cit_count), text]))
                        out.write("\n")

                    last_req = time.perf_counter()
            except ConnectionResetError as e:
                logger.info(f"ConnectionResetError at {url}")
            except Exception as e:
                trace = traceback.format_exc()
                logger.error(repr(e))
                logger.critical(trace)
    #            texts.append(text)
    #            authors.append(author)
    #            titles.append(title)
    #            cit_counts.append(cit_count)
