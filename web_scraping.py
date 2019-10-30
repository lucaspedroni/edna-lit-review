#!/usr/bin/env python3

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
    import re
    import sys
    import logging
    
    import requests
    import scholarly
    from bs4 import BeautifulSoup
    
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
        
    valid_text = re.compile(r"[Ee]nvironmental|DNA")
    
    headers = requests.utils.default_headers()
    headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    
    query = scholarly.search_pubs_query("environmental DNA")
    
#    texts = []
#    authors = []
#    titles = []
#    cit_counts = []
    with open("gs_scrape_results", "w") as out:
        for query_result in query:
            try:
                title = query_result.bib["title"]
                author = query_result.bib["author"] 
                cit_count = query_result.citedby
                
                result = requests.get(query_result.bib['url'], headers=headers)
                
                soup = BeautifulSoup(result.content)
                text = extract_natural_text(soup.find_all("p"))
                
                # more validation here:
                if valid_text.search(text):
                    out.write("\t".join([author, title, cit_count, text]))
                    out.write("\n")
            except Exception as e:
                trace = traceback.format_exc()
                logger.error(repr(e))
                logger.critical(trace)
    #            texts.append(text)
    #            authors.append(author)
    #            titles.append(title)
    #            cit_counts.append(cit_count)