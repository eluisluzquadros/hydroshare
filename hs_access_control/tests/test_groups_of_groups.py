

from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_access_control.models import PrivilegeCodes, GroupGroupPrivilege, GroupGroupProvenance

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set

from pprint import pprint


class T05CreateGroup(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T05CreateGroup, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        # user 'dog' create a new group called 'arfers'
        self.arfers = self.dog.uaccess.create_group(
            title='arfers',
            description="This is the arfers group",
            purpose="Our purpose to collaborate on barking.")

        # user 'cat' creates a new group called 'meowers'
        self.meowers = self.cat.uaccess.create_group(
            title='meowers',
            description="This is the meowers group",
            purpose="Our purpose to collaborate on begging.")

        self.cat.uaccess.share_group_with_user(self.meowers, self.dog, PrivilegeCodes.VIEW)

    def test_01_share_group_with_group(self):
        " share group with group, in allowed direction "

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_group_with_group(self.arfers, self.meowers, 
                                                                    PrivilegeCodes.VIEW))
        self.assertTrue(self.dog.uaccess.can_share_group_with_group(self.arfers, self.meowers, 
                                                                    PrivilegeCodes.CHANGE))
        self.assertTrue(self.dog.uaccess.can_share_group_with_group(self.meowers, self.arfers, 
                                                                    PrivilegeCodes.VIEW))
        self.assertFalse(self.dog.uaccess.can_share_group_with_group(self.meowers, self.arfers, 
                                                                     PrivilegeCodes.CHANGE))

        # share a group with a group
        # sharing "arfers" with "meowers" means that "meowers" is a member of "arfers" 
        # dog must own "arfers" and must have access to "meowers"

        self.dog.uaccess.share_group_with_group(self.arfers, self.meowers, PrivilegeCodes.VIEW)

        # privilege object created
        ggp = GroupGroupPrivilege.objects.get(group_s=self.arfers, group_w=self.meowers)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        # provenance object created
        ggp = GroupGroupProvenance.objects.get(group_s=self.arfers, group_w=self.meowers)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        # Group.gaccess.get_effective_privilege is polymorphic
        # and handles both user and group privilege now
        self.assertEqual(self.arfers.gaccess.get_effective_privilege(self.meowers),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.meowers.gaccess.get_effective_privilege(self.arfers),
                         PrivilegeCodes.NONE)

        self.assertTrue(self.meowers in self.arfers.gaccess.group_members)
        self.assertTrue(self.arfers not in self.meowers.gaccess.group_members)

        # TODO: next code cascading privilege in access control:
        # groupA is a member of groupB and groupB has access means groupA has access.

        self.assertFalse(self.dog.uaccess.can_share_group_with_group(self.arfers, self.meowers, 
                                                                     PrivilegeCodes.OWNER))
        with self.assertRaises(PermissionDenied): 
             self.dog.uaccess.share_group_with_group(self.arfers, self.meowers, 
                                                     PrivilegeCodes.OWNER)

        # Privileges are unchanged by the previous act
        self.assertEqual(self.arfers.gaccess.get_effective_privilege(self.meowers),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.meowers.gaccess.get_effective_privilege(self.arfers),
                         PrivilegeCodes.NONE)

        # upgrade share privilege 
        self.dog.uaccess.share_group_with_group(self.arfers, self.meowers, PrivilegeCodes.CHANGE)

        # privilege object created
        ggp = GroupGroupPrivilege.objects.get(group_s=self.arfers, group_w=self.meowers)
        self.assertEqual(ggp.privilege, PrivilegeCodes.CHANGE)

        # provenance object created
        ggp = GroupGroupProvenance.objects.filter(group_s=self.arfers, group_w=self.meowers)
        self.assertEqual(ggp.count(), 2)

        # Group.gaccess.get_effective_privilege is polymorphic
        # and handles both user and group privilege now
        self.assertEqual(self.arfers.gaccess.get_effective_privilege(self.meowers),
                         PrivilegeCodes.CHANGE)
        self.assertEqual(self.meowers.gaccess.get_effective_privilege(self.arfers),
                         PrivilegeCodes.NONE)

        # unshare group with group 
        self.assertTrue(self.dog.uaccess.can_unshare_group_with_group(self.arfers, self.meowers))
        self.dog.uaccess.unshare_group_with_group(self.arfers, self.meowers)

        # Group.gaccess.get_effective_privilege is polymorphic
        # and handles both user and group privilege now
        self.assertEqual(self.arfers.gaccess.get_effective_privilege(self.meowers),
                         PrivilegeCodes.NONE)
        self.assertEqual(self.meowers.gaccess.get_effective_privilege(self.arfers),
                         PrivilegeCodes.NONE)


    def test_01_undo_group_with_group(self):
        " share group with group with undo "
        self.assertTrue(self.dog.uaccess.can_share_group_with_group(self.arfers, self.meowers, 
                                                                    PrivilegeCodes.CHANGE))
        self.dog.uaccess.share_group_with_group(self.arfers, self.meowers, 
                                                    PrivilegeCodes.CHANGE)
        
        self.assertEqual(self.arfers.gaccess.get_effective_privilege(self.meowers),
                         PrivilegeCodes.CHANGE)
        self.assertEqual(self.meowers.gaccess.get_effective_privilege(self.arfers),
                         PrivilegeCodes.NONE)

