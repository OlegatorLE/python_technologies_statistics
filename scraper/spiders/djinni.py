from typing import Generator

import scrapy
from scrapy.http import Response

from scraper.items import JobItem


class DjinniSpider(scrapy.Spider):
    name = "djinni"
    allowed_domains = ["djinni.co"]
    start_urls = ["https://djinni.co/jobs/?primary_keyword=Python"]

    def parse(self, response: Response, **kwargs):
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

    def _parse_job_details(self, response: Response) -> Generator[dict, None, None]:
        technologies = response.css(
            ".job-additional-info--item-text span[class='']::text"
        ).getall()
        title = response.css("h1::text").get().replace("\n", " ").strip()
        company = response.css(
            ".job-details--title::text"
        ).get().replace("\n", " ").strip()
        yield JobItem(
            title=title,
            company=company,
            url=response.url,
            technologies=self.clean_technologies(technologies)
        )

    @staticmethod
    def clean_technologies(tech_list) -> list:
        # Видалення слова "Python" і видалення дублікатів
        tech_list = [tech for tech in tech_list if tech.lower() != 'python']
        return list(set(tech_list))
