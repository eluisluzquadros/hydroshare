"""This lists all the large resources and their statuses.
   This helps in checking that they download properly.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_tracking.models import Variable


class Command(BaseCommand):
    help = "debug the tracking log"

    def handle(self, *args, **options):
        for v in Variable.objects.filter(Q(name='visit') |
                                         Q(name='download') |
                                         Q(name='app_launch'))\
                .exclude(session__visitor__user=None):

            user = v.session.visitor.user
            value = v.get_value()
            name = v.name
            print("user={} name={} value={}".format(user.id, name, value))
