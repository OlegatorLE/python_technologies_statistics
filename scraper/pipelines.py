import django

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from twisted.internet import threads
from web.models import Job, Technology

django.setup()


class JobPipeline:
    def process_item(self, item, spider):
        return threads.deferToThread(self.handle_item, item, spider)

    def handle_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            job, created = Job.objects.get_or_create(
                title=adapter['title'],
                company=adapter['company'],
                defaults={'url': adapter['url']}
            )
            for tech in adapter.get('technologies', []):
                technology, _ = Technology.objects.get_or_create(name=tech)
                job.technologies.add(technology)
            return item
        except Exception as e:
            raise DropItem(f"Error saving item: {e}")