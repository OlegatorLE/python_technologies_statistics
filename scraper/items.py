# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobItem(scrapy.Item):
    date_posted = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    url = scrapy.Field()
    technologies = scrapy.Field()
