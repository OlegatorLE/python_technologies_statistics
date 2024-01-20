from celery import shared_task
from django.core.management import call_command


@shared_task
def run_spider(technologies):
    call_command('runspider', technologies)
