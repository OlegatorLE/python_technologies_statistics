from typing import Generator

import scrapy
import config
from scrapy.http import Response

from scraper.items import JobItem
from scraper.clean_technologies import clean_technologies


class DjinniSpider(scrapy.Spider):
    name = "djinni"
    allowed_domains = ["djinni.co"]
    start_urls = ["https://djinni.co/jobs/?primary_keyword=Python"]

    def parse(self, response: Response, **kwargs) -> Generator[
        scrapy.Request, None, None
    ]:
        for job in response.css(".job-list-item"):
            details_url = job.css("a.job-list-item__link::attr(href)").get()
            yield scrapy.Request(
                url=response.urljoin(details_url),
                callback=self._parse_job_details
            )

        next_page = response.css(
            "li.page-item:last-child a.page-link::attr(href)"
        ).get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    @staticmethod
    def _parse_technology_from_description(self, response: Response) -> list:
        desc = response.css(".row-mobile-order-2 ::text").getall()
        desc_text = " ".join(desc)
        technologies_found = [
            tech for tech in config.allowed_technologies
            if tech.lower() in desc_text.lower()
        ]
        return technologies_found

    def _parse_job_details(
            self, response: Response
    ) -> Generator[JobItem, None, None]:
        technologies = self._parse_technology_from_description(response)
        title = response.css("h1::text").get().replace("\n", " ").strip()
        company = response.css(
            ".job-details--title::text"
        ).get().replace("\n", " ").strip()
        yield JobItem(
            title=title,
            company=company,
            url=response.url,
            technologies=clean_technologies(technologies)
        )
