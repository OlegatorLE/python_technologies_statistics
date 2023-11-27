import os
import sys
import django

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'python_technologies_statistics.settings'

django.setup()

from web.models import Job, Technology
from scraper.spiders.djinni import DjinniSpider


process = CrawlerProcess(get_project_settings())
process.crawl(DjinniSpider)
process.start()
