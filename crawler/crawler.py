# from _typeshed import Self
from bs4 import BeautifulSoup
import pymongo
import urllib.parse
import requests
import sys


class Crawler():

    client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
    db = client.results

    def start_crawl(self, url, depth):

        robots_url = urllib.parse.urljoin(url, '/robots.txt')

        try:
            robots = requests.get(robots_url)
        except:
            print("robots not found!!!")
            self.crawl(url, depth)

        soup = BeautifulSoup(robots.text, 'lxml')

        content = soup.find('p')

        disallowed_links = []

        for word in content:
            if word[0] == '/':
                disallowed_links.append(urllib.parse.join(url, word))
                print("robots found and disallow.......")

        self.crawl(url, depth, disallowed_links)

    def crawl(self, url, depth, *disallowed_links):
        try:
            print(f"crawling url {url} at depth: {depth}")
            response = requests.get(url)
        except:
            print(f"failed to perform HTTP GET request on {url}")
            return

        soup = BeautifulSoup(response.text, 'lxml')

        try:
            title = soup.find('title').text
            description = ''

            for tag in soup.findAll():
                if tag.name == 'p':
                    description += tag.text.strip().replace('\n', '')

        except:
            print("failed to retrive title and description")
            return

        query = {
            'url': url,
            'title': title,
            'description': description,
        }

        search_results = self.db.search_results
        search_results.insert_one(query)
        search_results.create_index(
            [
                ('url', pymongo.TEXT),
                ('title', pymongo.TEXT),
                ('desciption', pymongo.TEXT),
            ],
            name='search_results',
            default_language='english'

        )

        if depth == 0:
            return

        links = soup.findAll('a')

        for link in links:
            try:
                if link['href'] not in disallowed_links:
                    if 'http' in link['href']:
                        self.crawl(link['href'], depth-1, disallowed_links)
                    else:
                        link['href'] = urllib.parse.urljoin(url, link['href'])
                        self.crawl(link['href'], depth-1, disallowed_links)
            except:
                print("no links retrived from the page")
                pass

        self.client.close()


spider = Crawler()
spider.start_crawl(
    sys.argv[1], int(sys.argv[2])


)

# run mongod in powershell the on mongodb compass then python crawler.py http://www.wikipedia.org/ 1  in terminal
