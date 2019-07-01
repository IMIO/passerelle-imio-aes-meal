from django.core.management.base import BaseCommand, CommandError
from passerelle_imio_ts1_datasources.models import MotivationTerm, DestinationTerm
import json


class Command(BaseCommand):
    help = 'Import TS1 Motivationterms in TS2.'

    def add_arguments(self, parser):
        parser.add_argument('--motivationterms_filepath', type=str)
        parser.add_argument('--destinationterms_filepath', type=str)
        parser.add_argument('--remove_all_terms', action='store_true')

    def handle(self, *args, **options):
        motivationterms_filepath = options['motivationterms_filepath']
        destinationterms_filepath = options['destinationterms_filepath']
        remove_all_terms = options['remove_all_terms']
        if remove_all_terms is True:
            self.remove_all_terms()
        if motivationterms_filepath is not None:
            self.motivationterms_import(motivationterms_filepath)
        if destinationterms_filepath is not None:
            self.destinationterms_import(destinationterms_filepath)

    def remove_all_terms(self):
        MotivationTerm.objects.all().delete()
        DestinationTerm.objects.all().delete()

    def motivationterms_import(self, path):
        data = {}
        with open(path) as data_file:
            data = json.load(data_file)
            for motivationterm in data:
                mt_object = MotivationTerm(text=motivationterm["text"],
                                           slug=motivationterm["slug"],
                                           price=motivationterm["price"],
                                           description=motivationterm["description"])
                mt_object.save()

    def destinationterms_import(self, path):
        data = {}
        with open(path) as data_file:
            data = json.load(data_file)
            for destinationterm in data:
                mt_object = DestinationTerm(text=destinationterm["text"],
                                            slug=destinationterm["slug"],
                                            price=destinationterm["price"],
                                            description=destinationterm["description"],
                                            paymentrequired=destinationterm["paymentRequired"])
                mt_object.save()
