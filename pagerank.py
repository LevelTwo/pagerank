import urllib
import urlparse
import random
from bs4 import BeautifulSoup
from collections import defaultdict

# http://wolfprojects.altervista.org/articles/change-urllib-user-agent/


class MyOpener(urllib.FancyURLopener):
   version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15'


def domain(url):
    # urlparse breaks down the url passed it, and you split the hostname up
    # Ex: hostname="www.google.com" becomes ['www', 'google', 'com']
    hostname = urlparse.urlparse(url).hostname.split(".")
    hostname = ".".join(len(hostname[-2]) < 4 and hostname[-3:] or hostname[-2:])
    return hostname

# This function will return all the urls on a page, and return the start url if there is an error or no urls


def parse_links(url, url_start):
    url_list = []
    myopener = MyOpener()
    try:
        # open, read, and parse the text using beautiful soup
        page = myopener.open(url)
        text = page.read()
        page.close()
        soup = BeautifulSoup(text, "lxml")

        # find all hyperlinks using beautiful soup
        for tag in soup.findAll('a', href=True):
            # concatenate the base url with the path from the hyperlink
            tmp = urlparse.urljoin(url, tag['href'])
            # we want to stay in the berkeley domain. This becomes more relevant later
            if domain(tmp).endswith('berkeley.edu'):
                url_list.append(tmp)
        if len(url_list) == 0:
            return [url_start]
        return url_list
    except:
        return [url_start]


url_start = "https://en.wikipedia.org/wiki/Probability"
myopener = MyOpener()
page = myopener.open(url_start)
current_url = page.geturl()
url_start = current_url
page.close()
num_of_visits = 500


def parse_links2(url, url_start):
    url_list = []
    myopener = MyOpener()
    try:
        # open, read, and parse the text using beautiful soup
        page = myopener.open(url)
        text = page.read()
        page.close()
        soup = BeautifulSoup(text, "lxml")

        # find all hyperlinks using beautiful soup
        for tag in set(soup.find("div", {"class": "mw-content-ltr"}).findAll("a", href=True)):
            # concatenate the base url with the path from the hyperlink
            tmp = urlparse.urljoin(url, tag['href'])
            # we want to stay in the berkeley domain. This becomes more relevant later
            if ':' not in tag['href'] and '#' not in tag['href']:
                url_list.append(tmp)
        if len(url_list) == 0:
            return [url_start]
        return url_list
    except:
        return [url_start]

# List of professors obtained from the EECS page
# Bad URLs help take care of some pathologies that ruin our surfing

# Creating a dictionary to keep track of how often we come across a professor
pagesdict = defaultdict(int)

for i in range(num_of_visits):
    if random.random() < 0.95:
        url_list = parse_links2(current_url, url_start)
        current_url = random.choice(url_list)
        myopener = MyOpener()
        page = myopener.open(current_url)
        text = page.read()
        soup = BeautifulSoup(text, 'lxml')
        current_url_title = soup.title.text
        print i, 'Visited...', current_url_title
        page.close()
        hrefs = soup.find("div", {"class": "mw-content-ltr"}).findAll("a", href=True)
        for a in set(hrefs):
            if "/wiki/" in str(a):
                pagesdict[a["href"].strip('/wiki/')] += 1
    else:
        # click the "home" button!
        current_url = url_start

pagesdict = {k: v for (k, v) in pagesdict.iteritems() if v > 1 and ':' not in k} # ':' to remove all stuff like Help:Category

for x in pagesdict.items():
    print x

page_ranks = [pair[0] for pair in sorted(pagesdict.items(), key=lambda item: item[1], reverse=True)]
top_score = pagesdict[page_ranks[0]]
for i in range(len(page_ranks)):
    print "%d %f: %s" % (i+1, pagesdict[page_ranks[i]]/top_score, page_ranks[i])
