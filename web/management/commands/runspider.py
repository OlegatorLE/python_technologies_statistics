from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraper.spiders.djinni import DjinniSpider


class Command(BaseCommand):
    help = 'Run the Scrapy spider'

    def add_arguments(self, parser):
        parser.add_argument(
            "technologies",
            nargs="+",
            type=str,
            help="List of technologies"
        )

    def handle(self, *args, **options):
        technologies = options["technologies"]
        process = CrawlerProcess(get_project_settings())
        process.crawl(DjinniSpider, technologies=technologies)
        process.start()
