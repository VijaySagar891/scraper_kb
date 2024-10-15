from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString
import json
import scrapy
from fastapi_cli.cli import callback
from scrapy.http import Response

# Find H1. Apollo.io and Hubspot both use this as article title.
# Hubspot: articleBody
# Frontegg: content-body

class KnowledgeBaseSpider(scrapy.Spider):
    name = 'kb_spider'
    start_urls = ['https://knowledge.hubspot.com/get-started']
    completed_urls = set()

    def isRelevantUrl(self, url: str):
        if url.startswith('https://knowledge.hubspot.com'):
            return True
        return False


    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.url in self.completed_urls:
            return

        if not self.isRelevantUrl(response.url):
            return

        self.completed_urls.add(response.url)
        # Get the last path segment and use it as the name of the page.
        page_name:str = response.url.split('/')[-1]
        if page_name == '':
            return

        soup = BeautifulSoup(response.text, "lxml")
        document_title = soup.h1.text

        text: str = ''
        images: list[str] = []
        urls: list[str] = []

        document_div = soup.find(attrs={"itemprop": "articleBody"})
        if document_div:
            for strings in document_div.stripped_strings:
                if len(text) > 0 and text[-1] != ' ' and len(strings) > 0 and strings[0] != ' ':
                    text += ' '
                text += strings
            for img in document_div.find_all("img"):
                images.append(img['src'])
            for url in document_div.find_all("a"):
                if url.get('href', '') != '':
                    url_href = url['href']
                    if url_href.startswith("/"):
                        url_href = urljoin(response.url, url_href)
                    if 'knowledge.hubspot' in url_href:
                        urls.append(url_href)

        with open("/home/vijay/Documents/hubspot_kb.json", "a+") as file_output:
            json_doc = {'url': response.url, 'title': document_title, 'text': text, 'urls': urls, 'images': images}
            json.dump(json_doc, file_output)
            file_output.write(',')

        # Pages to follow.
        for href in response.css("li.category-tile-wrapper a::attr(href)"):
            yield response.follow(href, callback=self.parse)
        for href in response.css("a.kb-link::attr(href)"):
            yield response.follow(href, callback=self.parse)
        for url in urls:
            yield response.follow(url, callback=self.parse)
