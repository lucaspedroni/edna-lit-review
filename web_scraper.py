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

def robots_allowed(url, logger):
    # robotparser has issues with this path for some reason. 
    # This path is allowed and has lots of articles, so doing this manually
    if re.search(r"onlinelibrary\.wiley\.com/doi/abs/", url):
        return True
    
    # extract base domain
    netloc = urlparse(url).netloc
    
    robot_parser = urllib.robotparser.RobotFileParser()
    robot_parser.set_url(f"http://{netloc}/robots.txt")
    robot_parser.read()

    if robot_parser.can_fetch("*", url):
        return True
    else:
        logger.info(f"Disallowed from {netloc}, {url}")
        return False

def extract_natural_text(result):
        soup = BeautifulSoup(result.content, features="html5lib")
        text = soup.find_all("p")
        text = [" ".join([str(it).strip() for it in item.contents]) for item in text]
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
    formatter = logging.Formatter("DEBUG%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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

    valid_text = re.compile(r"[Ee]nvironmental|DNA")
    
    headers = requests.utils.default_headers()
    headers["User-Agent"] = config.get("scraper", "user_agent")
    
    query = scholarly.search_pubs_query("environmental DNA")
    
    # Check timing of requests
    last_req = time.perf_counter()

    with open("gs_scrape_results", "w") as out:
        for query_result in query:
            try:
                if time.perf_counter() - last_req < 1:
                    time.sleep(1)

                title = query_result.bib["title"]
                author = query_result.bib["author"] 
                cit_count = query_result.citedby
                url = query_result.bib['url']

                if robots_allowed(url, logger):
                    result = requests.get(url, headers=headers)
                    
                    text = extract_natural_text(result)

                    # maybe need more validation at this step:
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

