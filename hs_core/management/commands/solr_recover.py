"""This re-indexes resources in SOLR to fix problems during SOLR builds.
* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from haystack import connection_router, connections
from haystack.query import SearchQuerySet
from haystack.exceptions import NotHandled
from pysolr import SolrError
import logging


def has_subfolders(resource):
    for f in resource.files.all():
        if '/' in f.short_path:
            return True
    return False


def vacuum_solr():
    """ Delete SOLR entries for resources that no longer exist """
    ids = list(SearchQuerySet().all().values_list('id', flat=True))
    for id in ids:
        fields = id.split('.')
        number = int(fields[len(fields)-1])
        result = BaseResource.objects.filter(id=number)
        if not result:
            print("did not find resource {} in Django: deleting from SOLR".format(id))
            for backend in connections:
                try:
                    backend.remove(id)
                except (IOError, SolrError) as e:
                    print("Failure: delete of %s with id %s failed: %s.", id,  e)


def repair_solr(short_id):
    """ Repair SOLR index content for a resource """

    logger = logging.getLogger(__name__)
    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    # instance with proper type
    instance = res.get_content_model()
    assert instance, (res, res.content_model)

    print("re-indexing {} in solr".format(short_id))

    # instance of BaseResource matching real instance
    baseinstance = BaseResource.objects.get(pk=instance.pk)
    basesender = BaseResource
    using_backends = connection_router.for_write(instance=baseinstance)
    for using in using_backends:
        # if object is public/discoverable or becoming public/discoverable, index it
        if instance.raccess.public or instance.raccess.discoverable:
            try:
                index = connections[using].get_unified_index().get_index(basesender)
                index.update_object(baseinstance, using=using)
            except NotHandled:
                logger.exception(
                    "Failure: changes to %s with short_id %s not added to Solr Index.",
                    str(type(instance)), baseinstance.short_id)

        # if object is private or becoming private, delete from index
        else:
            try:
                index = connections[using].get_unified_index().get_index(basesender)
                index.remove_object(baseinstance, using=using)
            except NotHandled:
                logger.exception("Failure: delete of %s with short_id %s failed.",
                                 str(type(instance)), baseinstance.short_id)


class Command(BaseCommand):
    help = "Repair SOLR index for a set of resources"

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

        parser.add_argument(
            '--type',
            dest='type',
            help='limit to resources of a particular type'
        )

        parser.add_argument(
            '--storage',
            dest='storage',
            help='limit to specific storage medium (local, user, federated)'
        )

        parser.add_argument(
            '--access',
            dest='access',
            help='limit to specific access class (public, discoverable, private)'
        )

        parser.add_argument(
            '--has_subfolders',
            action='store_true',  # True for presence, False for absence
            dest='has_subfolders',  # value is options['has_subfolders']
            help='limit to resources with subfolders',
        )

        parser.add_argument(
            '--vacuum',
            action='store_true',  # True for presence, False for absence
            dest='vacuum',  # value is options['vacuum']
            help='remove resources in SOLR that are not in Django',
        )

    def repair_filtered_solr(self, resource, options):
        if (options['type'] is None or resource.resource_type == options['type']) and \
           (options['storage'] is None or resource.storage_type == options['storage']) and \
           (options['access'] != 'public' or resource.raccess.public) and \
           (options['access'] != 'discoverable' or resource.raccess.discoverable) and \
           (options['access'] != 'private' or not resource.raccess.discoverable) and \
           (not options['has_subfolders'] or has_subfolders(resource)):
            storage = resource.get_irods_storage()
            if storage.exists(resource.root_path):
                repair_solr(resource.short_id)
            else:
                print("{} does not exist in iRODS".format(resource.short_id))

    def handle(self, *args, **options):
        if options['vacuum']:
            vacuum_solr()
        elif len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                resource = get_resource_by_shortkey(rid)
                self.repair_filtered_solr(resource, options)

        else:
            for resource in BaseResource.objects.all():
                self.repair_filtered_solr(resource, options)
