# To run this program run 'python pagerank.py [n_pages to crawl] [jsonfile]'

import json
import random
import sys
import threading
import time
import urllib
import urlparse

from bs4 import BeautifulSoup
from collections import defaultdict, deque

# Sort disease_conditions by current pagerank value
# ranked_diseases = sorted(diseases_conditions.items(), key=itemgetter(1))

# Rank symptoms by order of significance
# sorted(symptoms_dict, key=itemgetter(1), reverse=True)


class Worker(threading.Thread):

    def __init__(self, url, last10, N, thread_num):
        """
        Constructor.

        @param urls list of urls to check
        @param output file to write urls output
        """
        threading.Thread.__init__(self)
        self.url = url
        self.last10 = last10
        self.N = N
        self.thread_num = thread_num
        self.pagesdict = defaultdict(int)
        self.all_links = set([url])


    def run(self):
        """
        Thread run method. Check URLs one by one.
        """
        current_url = self.url
        while self.N:
            self.N -= 1
            if random.random() < 0.95 and len(set(self.last10)) > 4:
                try:
                    # list of urls with words in stopwords filtered out
                    soup, url_list = self.parse_links(current_url, self.url)
                    url_list = filter(lambda link: sum([word in link for word in stopwords]) == 0, url_list)
                    current_url = random.choice(url_list)
                    current_url_title = soup.title.text.strip()[:-14]  # removes MayoClinic
                    print 'Thread', self.thread_num, 'has', self.N, 'more links to go!', 'Currently visiting', current_url_title, '(' + str(len(url_list)), 'links)'
                    hrefs = soup.find("div", {"class": "contentbox links show-more"}).findAll("a", href=True)

                    # count href only if it is a symptom
                    for a in set(hrefs):
                        if '/symptoms/' in a["href"]:
                            self.pagesdict[a.text.lower()] += 1
                except:
                    current_url = random.sample(self.all_links, 1)[0]
            else:
                # click the "home" button!
                current_url = random.sample(self.all_links, 1)[0]

            self.last10.popleft()
            self.last10.append(current_url)
            self.all_links.add(current_url)

    def parse_links(self, url, url_start):
        url_list = []
        # open, read, and parse the text using beautiful soup
        try:
            page = urllib.urlopen(url)
            text = page.read()
            page.close()
            soup = BeautifulSoup(text, "lxml")
            # find all hyperlinks using beautiful soup
            hrefs = soup.find("div", {"class": "contentbox links show-more"}).findAll("a", href=True)
            for tag in set(hrefs):
                # concatenate the base url with the path from the hyperlink
                if tag['href'].startswith('/symptoms/') or tag['href'].startswith('/diseases-conditions/'):
                    tmp = urlparse.urljoin(url, tag['href'])
                    url_list.append(tmp)
            if len(url_list) == 0:
                return soup, [url_start]
            return soup, url_list
        except:
            return None, [url_start]

num_of_visits = 12 if len(sys.argv) < 2 else int(sys.argv[1])
stopwords = ['video', 'media', '#']
pagesdict = defaultdict(int)

if len(sys.argv) > 2:
    # read dictionary from json file
    with open(sys.argv[2], 'r') as file:
        jsondict = json.load(file)
    for key, val in jsondict.items():
        pagesdict[key] = val

url_start1 = "http://www.mayoclinic.org/symptoms/cough/basics/definition/sym-20050846"
url_start2 = "http://www.mayoclinic.org/symptoms/nausea/basics/definition/sym-20050736"
url_start3 = "http://www.mayoclinic.org/diseases-conditions/carbon-monoxide/basics/definition/con-20025444"
url_start4 = "http://www.mayoclinic.org/diseases-conditions/heart-attack/basics/definition/con-20019520"
start_links = [url_start1, url_start2, url_start3, url_start4]
workers = []
t = time.time()

for i, url_start in enumerate(start_links):
    worker = Worker(url_start, deque('0123456789'), num_of_visits / 4, i+1)
    worker.start()
    workers.append(worker)

for worker in workers:
    for key in worker.pagesdict:
        pagesdict[key] += worker.pagesdict[key]
    worker.join()

for x in pagesdict.items():
    print x

# write dictionary to json file
with open('symptoms.json', 'w') as file:
    file.write(json.dumps(pagesdict))

page_ranks = [pair[0] for pair in sorted(pagesdict.items(), key=lambda item: item[1], reverse=True)]
top_score = float(pagesdict[page_ranks[0]])
for i in range(len(page_ranks)):
    print "%d %f: %s" % (i+1, pagesdict[page_ranks[i]]/top_score, page_ranks[i])

print 'TOTAL TIME ELAPSED:', time.time() - t, 'seconds'
