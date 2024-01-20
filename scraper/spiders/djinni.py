import re
from datetime import datetime
from typing import Generator, List

import scrapy
from scrapy.http import Response

import config
from scraper.items import JobItem


class DjinniSpider(scrapy.Spider):
    name = "djinni"
    allowed_domains = ["djinni.co"]

    def __init__(self, technologies: List[str] = None, *args, **kwargs):
        super(DjinniSpider, self).__init__(*args, **kwargs)
        if technologies is None or not isinstance(technologies, list):
            raise ValueError("Technologies should be a list")
        self.start_urls = [self.create_url(tech) for tech in technologies]

    @staticmethod
    def create_url(technology: str) -> str:
        return f"https://djinni.co/jobs/?primary_keyword={technology}"

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
        english = self._parse_english_level(response)
        experience = self._parse_years_of_experience(response)
        yield JobItem(
            title=title,
            date_posted=date_posted,
            company=company,
            url=response.url,
            english=english,
            experience=experience,
            technologies=technologies
        )

    @staticmethod
    def _parse_years_of_experience(response: Response) -> int:
        for job_info in response.css(".job-additional-info--item"):
            experience_text = job_info.css(
                ".job-additional-info--item-text::text").get()

            if experience_text:
                match = re.search(r"(\d+)\s+(?:рік|роки|років)",
                                  experience_text)
                if match:
                    return match.group(1)

        return 0

    @staticmethod
    def _parse_english_level(response: Response):
        english = "Not Specified"
        for job_info in response.css(".job-additional-info--item"):
            english_level_text = job_info.css(
                ".job-additional-info--item-text::text").get()
            if english_level_text and "Англійська" in english_level_text:
                english = english_level_text.split(":")[-1].strip()
                break
        return english

    @staticmethod
    def _parse_technology_from_description(response: Response) -> list:
        desc = response.css(".row-mobile-order-2 ::text").getall()
        desc_text = " ".join(desc)
        technologies_found = [
            tech for tech in config.allowed_technologies_python
            if re.search(r'\b{}\b'.format(re.escape(tech)), desc_text,
                         re.IGNORECASE)
        ]
        return technologies_found

    def _parse_date_posted(self, response: Response) -> str:
        date_text = response.css("p.text-muted").extract_first()
        if "Вакансія" in date_text:
            date_posted = (
                date_text.split("Вакансія опублікована")[-1]
                .strip()
                .split("<br>")[0]
                .strip()
            )

            return self._translate_month_ua_to_en(date_posted)
        else:
            date_posted = (
                date_text.split("Job posted on")[-1]
                .strip()
                .split("<br>")[0]
                .strip()
            )
            date_object = datetime.strptime(date_posted, '%d %B %Y')
            return date_object.strftime('%Y-%m-%d')

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
        date_posted = date_object.strftime('%Y-%m-%d')

        return date_posted
