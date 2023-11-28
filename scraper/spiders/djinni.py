import locale
from datetime import datetime, date
from typing import Generator

import scrapy
import config
from scrapy.http import Response
from babel.dates import format_date, parse_date

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
                callback=self._parse_job_details,
            )

        next_page = response.css(
            "li.page-item:last-child a.page-link::attr(href)"
        ).get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def _parse_job_details(
            self, response: Response
    ) -> Generator[JobItem, None, None]:
        date_posted = self._parse_date_posted(response)
        technologies = self._parse_technology_from_description(response)
        title = response.css("h1::text").get().replace("\n", " ").strip()
        company = response.css(
            ".job-details--title::text"
        ).get().replace("\n", " ").strip()
        yield JobItem(
            title=title,
            date_posted=date_posted,
            company=company,
            url=response.url,
            technologies=technologies
        )

    @staticmethod
    def _parse_technology_from_description(response: Response) -> list:
        desc = response.css(".row-mobile-order-2 ::text").getall()
        desc_text = " ".join(desc)
        technologies_found = [
            tech for tech in config.allowed_technologies
            if tech.lower() in desc_text.lower()
        ]
        return technologies_found

    def _parse_date_posted(self, response: Response) -> str:
        date_text = response.css("p.text-muted").extract_first()
        date_posted = (
            date_text.split("Вакансія опублікована")[-1]
            .strip()
            .split("<br>")[0]
            .strip()
        )
        return self._translate_month_ua_to_en(date_posted)

    @staticmethod
    def _translate_month_ua_to_en(date_posted: str) -> str:
        months_ua_to_en = {
            'січня': '01',
            'лютого': '02',
            'березня': '03',
            'квітня': '04',
            'травня': '05',
            'червня': '06',
            'липня': '07',
            'серпня': '08',
            'вересня': '09',
            'жовтня': '10',
            'листопада': '11',
            'грудня': '12'
        }
        for ua_month, en_month in months_ua_to_en.items():
            if ua_month in date_posted:
                date_posted = date_posted.replace(ua_month, en_month)
                break

        date_object = datetime.strptime(date_posted, '%d %m %Y')

        date_posted = format_date(date_object, locale="en")

        return date_posted
