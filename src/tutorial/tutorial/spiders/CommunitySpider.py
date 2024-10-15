from fileinput import filename
from pathlib import Path
from typing import Iterable, Any

import scrapy
from scrapy import Request
from scrapy.http import Response


class CommunitySpider(scrapy.Spider):
    name = "community"
    start_urls = ['https://knowledge.hubspot.com/']
    completed_urls = set()
    page_count = 0

    def isRelevantUrl(self, url):
        for domain_url in self.start_urls:
            if url.startswith(domain_url):
                return True
        return False

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.url in self.completed_urls:
            return

        if not self.isRelevantUrl(response.url):
            return
        page_name = response.url.split("/")[-1]
        if page_name != '':
            contents = ''
            for text_section in response.css("div.blog-section *::text").getall():
                stripped_text = text_section.strip()
                if len(stripped_text) > 0:
                    if stripped_text[0].isupper():
                        contents += '\n'
                    contents += stripped_text
                    if stripped_text[-1] == '.' or stripped_text[-1] == ':':
                        contents += '\n'
                    else:
                        contents += ' '

            if len(contents) > 0:
                fp = open("crawled/" + page_name, "w")
                fp.write(contents)
                fp.close()

        print(response.url)
        for href in response.css("li.category-tile-wrapper a::attr(href)"):
            yield response.follow(href, callback=self.parse)
        for href in response.css("a.kb-link::attr(href)"):
            yield response.follow(href, callback=self.parse)

        self.completed_urls.add(response.url)