# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from audioop import cross

import scrapy


class TutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class KnowledgeBaseIem:
    def __init__(self, image_links: set[str], cross_links: set[str], text: str):
        self.image_links = image_links
        self.cross_links = cross_links
        self.text = text
