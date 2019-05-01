import os
import tempfile
import shutil

from hs_core.hydroshare import resource, get_resource_by_shortkey
from django.contrib.auth.models import Group, User
from hs_core.models import BaseResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from django.core.management import call_command
from django.test import TestCase

class ModifyResourceIdCommandTestCase(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(ModifyResourceIdCommandTestCase, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            middle_name='ì', # testing international character
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        # create files
        file_one = "test1.txt"
        file_two = "test2.tif"

        open(file_one, "w").close()
        open(file_two, "w").close()

        # open files for read and upload
        self.file_one = open(file_one, "r")
        self.file_two = open(file_two, "r")

        # Make a text file
        self.txt_file_path = os.path.join(self.tmp_dir, 'text.txt')
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.res = resource.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource',
            files=(self.file_one, self.file_two)
        )

    def tearDown(self):
        super(ModifyResourceIdCommandTestCase, self).tearDown()

        shutil.rmtree(self.tmp_dir)

        self.user.uaccess.delete()
        self.user.delete()
        self.hs_group.delete()

        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        self.file_one.close()
        os.remove(self.file_one.name)
        self.file_two.close()
        os.remove(self.file_two.name)

        if self.res:
            self.res.delete()

    def test_modify_resource_id(self):
        res_id = self.res.short_id
        args = [res_id]
        opts = {}
        call_command('modify_resource_id', *args, **opts)

        self.res.refresh_from_db()
        self.assertNotEqual(res_id, self.res.short_id)