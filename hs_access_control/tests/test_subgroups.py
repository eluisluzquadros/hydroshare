from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_access_control.models import PrivilegeCodes, GroupSubgroupPrivilege,\
    GroupSubgroupProvenance
from hs_access_control.models import access_provenance
from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


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

        self.cat2 = hydroshare.create_account(
            'cat2@gmail.com',
            username='cat2',
            first_name='not a dog',
            last_name='last_name_cat2',
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

        self.dog2 = hydroshare.create_account(
            'dog2@gmail.com',
            username='dog2',
            first_name='a little arfer',
            last_name='last_name_dog2',
            superuser=False,
            groups=[]
        )

        self.bat = hydroshare.create_account(
            'bat@gmail.com',
            username='bat',
            first_name='a little batty',
            last_name='last_name_bat',
            superuser=False,
            groups=[]
        )

        self.bat2 = hydroshare.create_account(
            'bat2@gmail.com',
            username='bat2',
            first_name='the ultimate bat',
            last_name='last_name_bat2',
            superuser=False,
            groups=[]
        )

        # user 'dog' create a new group called 'dogs'
        self.dogs = self.dog.uaccess.create_group(
            title='dogs',
            description="This is the dogs group",
            purpose="Our purpose to collaborate on barking."
        )
        self.dog.uaccess.share_group_with_user(self.dogs, self.dog2, PrivilegeCodes.VIEW)

        # user 'cat' creates a new group called 'cats'
        self.cats = self.cat.uaccess.create_group(
            title='cats',
            description="This is the cats group",
            purpose="Our purpose to collaborate on begging.")
        self.cat.uaccess.share_group_with_user(self.cats, self.cat2, PrivilegeCodes.VIEW)

        # user 'bat' creates a new group called 'bats'
        self.bats = self.bat.uaccess.create_group(
            title='bats',
            description="This is the bats group",
            purpose="Our purpose is to collaborate on guano.")
        self.bat.uaccess.share_group_with_user(self.bats, self.bat2, PrivilegeCodes.VIEW)

        # create a cross-over share that allows dog to share with cats.
        self.cat.uaccess.share_group_with_user(self.cats, self.dog, PrivilegeCodes.OWNER)
        # create a cross-over share that allows dog to share with bats.
        self.bat.uaccess.share_group_with_user(self.bats, self.dog, PrivilegeCodes.OWNER)

        self.holes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='all about dog holes',
            metadata=[],
        )
        self.dog.uaccess.share_resource_with_group(self.holes, self.dogs, 
                                                   PrivilegeCodes.VIEW)

        self.squirrels = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='a list of squirrels to pester',
            metadata=[],
        )
        self.dog.uaccess.share_resource_with_group(self.squirrels, self.dogs, 
                                                   PrivilegeCodes.CHANGE)
        self.posts = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='all about scratching posts',
            metadata=[],
        )
        self.cat.uaccess.share_resource_with_group(self.posts, self.cats, 
                                                   PrivilegeCodes.VIEW)
        self.claus = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='bad jokes about claws',
            metadata=[],
        )
        self.cat.uaccess.share_resource_with_group(self.claus, self.cats, PrivilegeCodes.CHANGE)

        self.wings = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.bat,
            title='things with wings',
            metadata=[],
        )
        self.bat.uaccess.share_resource_with_group(self.wings, self.bats, PrivilegeCodes.VIEW)

        self.perches = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.bat,
            title='where to perch',
            metadata=[],
        )
        self.bat.uaccess.share_resource_with_group(self.perches, self.bats, PrivilegeCodes.VIEW)
        
    def test_share_group_with_subgroup(self):
        " share group with group, in allowed direction "

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_group_with_subgroup(self.dogs, 
                                                                       self.cats,
                                                                       PrivilegeCodes.VIEW))
        self.assertTrue(self.dog.uaccess.can_share_group_with_subgroup(self.dogs, 
                                                                       self.cats,
                                                                       PrivilegeCodes.CHANGE))
        self.assertTrue(self.dog.uaccess.can_share_group_with_subgroup(self.cats, 
                                                                       self.dogs,
                                                                       PrivilegeCodes.VIEW))
        self.assertTrue(self.dog.uaccess.can_share_group_with_subgroup(self.cats, 
                                                                       self.dogs,
                                                                       PrivilegeCodes.CHANGE))
        self.assertFalse(self.cat.uaccess.can_share_group_with_subgroup(self.dogs, 
                                                                        self.cats,
                                                                        PrivilegeCodes.VIEW))
        self.assertFalse(self.cat.uaccess.can_share_group_with_subgroup(self.dogs, 
                                                                        self.cats,
                                                                        PrivilegeCodes.CHANGE))
        self.assertFalse(self.cat.uaccess.can_share_group_with_subgroup(self.cats, 
                                                                        self.dogs,
                                                                        PrivilegeCodes.VIEW))
        self.assertFalse(self.cat.uaccess.can_share_group_with_subgroup(self.cats, 
                                                                        self.dogs,
                                                                        PrivilegeCodes.CHANGE))

        # share a group with a group
        # sharing "dogs" with "cats" means that "cats" is a member of "dogs"
        # dog must own "dogs" and must have access to "cats"

        self.dog.uaccess.share_group_with_subgroup(self.dogs, self.cats, PrivilegeCodes.VIEW)

        # privilege object created
        ggp = GroupSubgroupPrivilege.objects.get(group=self.dogs, subgroup=self.cats)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        # provenance object created
        ggp = GroupSubgroupProvenance.objects.get(group=self.dogs, subgroup=self.cats)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        self.assertEqual(self.dogs.gaccess.get_effective_subgroup_privilege(self.cats),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.cats.gaccess.get_effective_subgroup_privilege(self.dogs),
                         PrivilegeCodes.NONE)

        self.assertTrue(self.holes in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)

        # print('dogs.member_groups')
        # pprint(list(self.dogs.gaccess.member_groups))
        # print('cats.member_groups')
        # pprint(list(self.cats.gaccess.member_groups))

        self.assertTrue(self.cats in self.dogs.gaccess.member_groups)
        self.assertTrue(self.dogs not in self.cats.gaccess.member_groups)

        self.assertTrue(self.holes in self.dogs.gaccess.view_resources)
        self.assertTrue(self.posts in self.cats.gaccess.view_resources)
        self.assertTrue(self.posts in self.dogs.gaccess.view_resources)
        self.assertTrue(self.holes not in self.cats.gaccess.view_resources)
        self.assertTrue(self.holes not in self.dogs.gaccess.edit_resources)
        self.assertTrue(self.posts not in self.cats.gaccess.edit_resources)
        self.assertTrue(self.posts not in self.dogs.gaccess.edit_resources)
        self.assertTrue(self.holes not in self.cats.gaccess.edit_resources)

        # check that resources are found correctly in groups
        self.assertTrue(self.posts in self.cats.gaccess.view_resources)
        self.assertTrue(self.holes in self.dogs.gaccess.view_resources)

        # TODO: next code cascading privilege in access control:
        # groupA is a member of groupB and groupB has access means groupA has access.

        self.assertFalse(self.dog.uaccess.can_share_group_with_subgroup(self.dogs, self.cats,
                                                                        PrivilegeCodes.OWNER))
        with self.assertRaises(PermissionDenied):
            self.dog.uaccess.share_group_with_subgroup(self.dogs, self.cats,
                                                       PrivilegeCodes.OWNER)

        # Privileges are unchanged by the previous act
        self.assertEqual(self.dogs.gaccess.get_effective_subgroup_privilege(self.cats),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.cats.gaccess.get_effective_subgroup_privilege(self.dogs),
                         PrivilegeCodes.NONE)

        # upgrade share privilege
        self.dog.uaccess.share_group_with_subgroup(self.dogs, self.cats, PrivilegeCodes.CHANGE)

        # privilege object created
        ggp = GroupSubgroupPrivilege.objects.get(group=self.dogs, subgroup=self.cats)
        self.assertEqual(ggp.privilege, PrivilegeCodes.CHANGE)

        # provenance object created
        ggp = GroupSubgroupProvenance.objects.filter(group=self.dogs, subgroup=self.cats)
        self.assertEqual(ggp.count(), 2)

        self.assertEqual(self.dogs.gaccess.get_effective_subgroup_privilege(self.cats),
                         PrivilegeCodes.CHANGE)
        self.assertEqual(self.cats.gaccess.get_effective_subgroup_privilege(self.dogs),
                         PrivilegeCodes.NONE)

        self.assertTrue(self.holes in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)

        # unshare group with group
        self.assertTrue(self.dog.uaccess.can_unshare_group_with_subgroup(self.dogs, self.cats))
        self.dog.uaccess.unshare_group_with_subgroup(self.dogs, self.cats)

        self.assertEqual(self.dogs.gaccess.get_effective_subgroup_privilege(self.cats),
                         PrivilegeCodes.NONE)
        self.assertEqual(self.cats.gaccess.get_effective_subgroup_privilege(self.dogs),
                         PrivilegeCodes.NONE)

        self.assertTrue(self.holes not in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)

    def test_undo_share_group_with_subgroup(self):
        " share group with group with undo "
        self.assertTrue(self.dog.uaccess.can_share_group_with_subgroup(self.dogs, self.cats,
                                                                       PrivilegeCodes.CHANGE))
        self.dog.uaccess.share_group_with_subgroup(self.dogs, self.cats,
                                                   PrivilegeCodes.CHANGE)

        self.assertEqual(self.dogs.gaccess.get_effective_subgroup_privilege(self.cats),
                         PrivilegeCodes.CHANGE)
        self.assertEqual(self.cats.gaccess.get_effective_subgroup_privilege(self.dogs),
                         PrivilegeCodes.NONE)

        self.assertTrue(self.dog.uaccess.can_undo_share_group_with_subgroup(self.dogs,
                                                                            self.cats))

        self.dog.uaccess.undo_share_group_with_subgroup(self.dogs, self.cats)

        self.assertEqual(self.dogs.gaccess.get_effective_subgroup_privilege(self.cats),
                         PrivilegeCodes.NONE)
        self.assertEqual(self.cats.gaccess.get_effective_subgroup_privilege(self.dogs),
                         PrivilegeCodes.NONE)

    def test_privilege_squashing(self):
        " sharing group with group squashes privileges as needed "

        self.assertTrue(self.holes not in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)

        # upgrade share privilege
        self.dog.uaccess.share_group_with_subgroup(self.dogs, self.cats,
                                                   PrivilegeCodes.CHANGE)

        # print(access_provenance(self.dog, self.posts))
        # print(access_provenance(self.dog2, self.posts))
        # print(access_provenance(self.cat, self.holes))
        # print(access_provenance(self.cat2, self.holes))

        self.assertTrue(self.holes in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW, via_user=True, via_group=False, via_subgroup=False))
        self.assertTrue(self.holes not in self.cat.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW, via_user=False, via_group=True, via_subgroup=False))

        self.assertTrue(self.holes in self.cat.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW, via_user=False, via_group=False, via_subgroup=True))

        # check the effects upon third party groups
        self.assertTrue(self.posts not in self.dog2.uaccess.view_resources)
        self.assertTrue(self.posts not in self.dogs.gaccess.edit_resources)
        self.assertTrue(self.posts in self.dog.uaccess.view_resources)
        self.assertTrue(self.posts not in self.dog.uaccess.edit_resources)

    def test_explicit_access(self):
        " sharing groups with groups changes explicit access returns "

        foo = self.cat.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
            via_user=False, via_group=False, via_subgroup=True)
        self.assertTrue(self.holes not in foo)

        self.dog.uaccess.share_group_with_subgroup(self.dogs, self.cats)

        foo = self.cat.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
            via_user=False, via_group=False, via_subgroup=True)
        self.assertTrue(self.holes in foo)
        foo = self.cat.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
            via_user=False, via_group=False, via_subgroup=True)
        self.assertTrue(self.holes not in foo)

        # unsquash CHANGE privilege 
        self.dog.uaccess.share_group_with_subgroup(self.dogs, self.cats, 
                                                   PrivilegeCodes.CHANGE)
        self.dog.uaccess.share_resource_with_group(self.holes, self.dogs, 
                                                   PrivilegeCodes.CHANGE)

        print(access_provenance(self.cat, self.holes))

        foo = self.cat.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
            via_user=False, via_group=False, via_subgroup=True)
        pprint(foo)
        self.assertTrue(self.holes not in foo)
        foo = self.cat.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
            via_user=False, via_group=False, via_subgroup=True)
        self.assertTrue(self.holes in foo)
