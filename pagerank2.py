# To run this program run 'python pagerank.py [n_pages to crawl] [jsonfile]'

from __future__ import division
import json
import random
import sys
import threading
import time
import urllib
import urlparse

from bs4 import BeautifulSoup
from collections import defaultdict, deque


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
        self.pagesdict = defaultdict(lambda: [[], 1])
        self.diseases = defaultdict(int)
        self.symptoms = defaultdict(int)
        self.all_links = set([url])
        self.max_links = 0

    def run(self):
        """
        Thread run method. Check URLs one by one.
        """
        current_url = self.url
        while max(self.N, 0):
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

                    if "/symptoms/" in current_url or "/diseases-conditions/" in current_url:
                        current_symptom_disease = current_url.split("http://www.mayoclinic.org")[1].split("/")[2]
                        if (self.pagesdict[current_symptom_disease][1] == 1):
                            # Keep track of links only if the current link is a symptom or disease,
                            # and if we haven't encountered this page before. If we haven't encountered
                            # the page before we need to update all relevant symptoms/diseases that are
                            # linked to by this page with this page.
                            related_symps_diseases = []
                            for a in set(hrefs):
                                split_link = a["href"].split("/")
                                if "symptoms" in split_link:
                                    symptom = split_link[2]
                                    related_symps_diseases.append(symptom)
                                    # Related link is a symptom.
                                    self.pagesdict[symptom][0].append(current_symptom_disease)
                                    self.symptoms[symptom] = 1
                                elif "diseases-conditions" in split_link:
                                    disease = split_link[2]
                                    related_symps_diseases.append(disease)
                                    # Related link is a disease or condition.
                                    self.pagesdict[disease][0].append(current_symptom_disease)
                                    self.diseases[disease] = 1
                            # Update the number of symptoms/diseases this page links to
                            num_links = len(set(related_symps_diseases))
                            self.pagesdict[current_symptom_disease][1] = num_links
                            if num_links > self.max_links:
                                self.max_links = num_links
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


def assign_page_rank(pagesdict, ranked_diseases, ranked_symptoms, max_links):
    """ Assign a page rank to each disease and symptom.
    (See http://infolab.stanford.edu/~taherh/papers/topic-sensitive-pagerank-tkde.pdf)
    Weightings should be different depending on what is
    referencing what.

    The more diseases that link to a disease, the less likely
    a symptom that is referenced by that disease will be indicative
    of the disease itself (the symptom could be a manifestation of some
    other related disease).

    The more symptoms that link to a disease, the less likely that any
    symptom referenced by that disease is a guarantee of the disease itself.

    The more diseases that link to a symptom, the less likely that having
    the symptom is indicative of any one disease.

    The more symptoms that link to a symptom, the less likely that the
    symptom by itself will provide much information about any given disease.

    Keyword arguments:
    pagesdict       -- a complete dictionary of all the pages
    ranked_diseases -- initialized rank dictionary of diseases
    ranked_symptoms -- initialized rank dictionary of symptoms
    """
    changing = True
    # old relative ranking
    old_ranks = [pair[0] for pair in sorted(ranked_diseases.items(), key=lambda item: item[1])]
    while changing:
        try:
            # If fewer than 5 disease pages change relative rank, then we can
            # say PageRank is finished.
            for key in pagesdict:
                new_rank = 1
                for link in pagesdict[key][0]:
                    if link in ranked_diseases:
                        # Link was from a disease.
                        new_rank += ranked_diseases[link]*(pagesdict[link][1]/max_links)
                    elif link in ranked_symptoms:
                        # Link was from a symptom.
                        new_rank += 0.25*ranked_symptoms[link]*(pagesdict[link][1]/max_links)
                if key in ranked_diseases:
                    # Looking at a disease. Assign the new rank.
                    ranked_diseases[key] = new_rank
                elif key in ranked_symptoms:
                    # Looking at a symptom. Assign the new rank.
                    ranked_symptoms[key] = new_rank
            # new relative ranking
            new_ranks = [pair[0] for pair in sorted(ranked_diseases.items(), key=lambda item: item[1])]
            num_rank_changes = 0
            changing = False
            for i in range(len(old_ranks)):
                if not old_ranks[i] == new_ranks[i]:
                    num_rank_changes += 1
                if num_rank_changes > 10:
                    # Page rank is not finished yet.
                    old_ranks = new_ranks
                    changing = True
                    break
        except:
            continue
    return ranked_symptoms

num_of_visits = 12 if len(sys.argv) < 2 else int(sys.argv[1])
stopwords = ['video', 'media', '#']
pagesdict = defaultdict(lambda: [set(), 1])
ranked_diseases = defaultdict(lambda: 1)
ranked_symptoms = defaultdict(lambda: 1)
max_external_links = 0

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
        pagesdict[key.replace('-', ' ')][0].update(worker.pagesdict[key][0])
        pagesdict[key][1] = max(pagesdict[key][1], worker.pagesdict[key][1])
    ranked_diseases.update(worker.diseases)
    ranked_symptoms.update(worker.symptoms)
    max_external_links = max(max_external_links, worker.max_links)
    worker.join()

for x in pagesdict.items():
    print x

# write dictionary to json file
# with open('symptoms.json', 'w') as file:
#     file.write(json.dumps(pagesdict))

ranked = assign_page_rank(pagesdict, ranked_diseases, ranked_symptoms, max_external_links)
page_ranks = [pair[0] for pair in sorted(ranked.items(), key=lambda item: item[1], reverse=True)]
top_score = float(ranked_symptoms[page_ranks[0]])
print top_score
for i in range(len(page_ranks)):
    print "%d %f: %s" % (i+1, ranked[page_ranks[i]]/top_score, page_ranks[i])

# page_ranks = [pair[0] for pair in sorted(pagesdict.items(), key=lambda item: item[1], reverse=True)]
# top_score = float(pagesdict[page_ranks[0]])
# for i in range(len(page_ranks)):
#     print "%d %f: %s" % (i+1, pagesdict[page_ranks[i]]/top_score, page_ranks[i])

print 'TOTAL TIME ELAPSED:', time.time() - t, 'seconds'
