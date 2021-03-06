"""
Handle ElasticSearch setup that needs to be done at bootstrap time.
"""
import logging

from django.core.management.base import BaseCommand

from ...index_manager import regenerate_indexes, store_es_scripts

logger = logging.getLogger("richie.core.bootstrap_elasticsearch")


class Command(BaseCommand):
    """
    Bootstrap tasks include:
    - create indices for courses, organizations, subjects,
    - index all records in their respective indices,
    - store necessary scripts.
    """

    help = __doc__

    def handle(self, *args, **options):
        # Keep track of starting time for logging purposes
        logger.info("Starting to regenerate ES indices...")

        # Creates new indices each time, populates them, and atomically replaces
        # the old indices once the new ones are ready.
        regenerate_indexes(logger)

        # Confirm operation success through a console log
        logger.info("ES indices regenerated.")

        logger.info("Starting to store ES scripts...")

        # Iterates over indexables to find all the necessary scripts and store them
        store_es_scripts(logger)

        logger.info("ES scripts stored.")
