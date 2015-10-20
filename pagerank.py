# To run this program run 'python pagerank.py [n_pages to crawl]'

import urllib
import urlparse
import random
import sys

from bs4 import BeautifulSoup
from collections import defaultdict


def parse_links(url, url_start):
    url_list = []
    try:
        # open, read, and parse the text using beautiful soup
        page = urllib.urlopen(url)
        text = page.read()
        page.close()
        soup = BeautifulSoup(text, "lxml")

        # find all hyperlinks using beautiful soup
        hrefs = soup.find("div", {"class": "contentbox links show-more"}).findAll("a", href=True)
        for tag in set(hrefs):
            # concatenate the base url with the path from the hyperlink
            tmp = urlparse.urljoin(url, tag['href'])
            url_list.append(tmp)
        if len(url_list) == 0:
            return [url_start]
        return url_list
    except:
        return [url_start]

# Creating a dictionary to keep track of how often we come across a professor
num_of_visits = 10 if len(sys.argv) < 2 else int(sys.argv[1])
stopwords = ['video', 'media', '#']
pagesdict = defaultdict(int)
url_start = "http://www.mayoclinic.org/symptoms/cough/basics/definition/sym-20050846"
current_url = url_start

for i in range(num_of_visits):
    if random.random() < 0.95:
        # list of urls with words in stopwords filtered out
        url_list = filter(lambda link: sum([word in link for word in stopwords]) == 0, parse_links(current_url, url_start))
        current_url = random.choice(url_list)
        page = urllib.urlopen(current_url)
        text = page.read()
        page.close()
        soup = BeautifulSoup(text, 'lxml')
        current_url_title = soup.title.text.strip()[:-14]  # removes MayoClinic
        print 'Link', i, current_url_title, '(' + str(len(url_list)), 'links)'
        hrefs = soup.find("div", {"class": "contentbox links show-more"}).findAll("a", href=True)

        # count href only if it is a symptom
        for a in set(hrefs):
            if '/symptoms/' in a["href"]:
                pagesdict[a.text.lower()] += 1
    else:
        # click the "home" button!
        current_url = url_start

for x in pagesdict.items():
    print x

page_ranks = [pair[0] for pair in sorted(pagesdict.items(), key=lambda item: item[1], reverse=True)]
top_score = pagesdict[page_ranks[0]]
for i in range(len(page_ranks)):
    print "%d %f: %s" % (i+1, pagesdict[page_ranks[i]]/top_score, page_ranks[i])
