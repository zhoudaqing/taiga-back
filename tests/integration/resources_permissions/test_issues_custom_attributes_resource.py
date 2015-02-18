# Copyright (C) 2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2015 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.custom_attributes import serializers
from taiga.permissions.permissions import MEMBERS_PERMISSIONS

from tests import factories as f
from tests.utils import helper_test_http_method

import pytest
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def data():
    m = type("Models", (object,), {})
    m.registered_user = f.UserFactory.create()
    m.project_member_with_perms = f.UserFactory.create()
    m.project_member_without_perms = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()
    m.other_user = f.UserFactory.create()
    m.superuser = f.UserFactory.create(is_superuser=True)

    m.public_project = f.ProjectFactory(is_private=False,
                                        anon_permissions=['view_project'],
                                        public_permissions=['view_project'],
                                        owner=m.project_owner)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=['view_project'],
                                          public_permissions=['view_project'],
                                          owner=m.project_owner)
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner)

    m.public_membership = f.MembershipFactory(project=m.public_project,
                                          user=m.project_member_with_perms,
                                          email=m.project_member_with_perms.email,
                                          role__project=m.public_project,
                                          role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.private_membership1 = f.MembershipFactory(project=m.private_project1,
                                                user=m.project_member_with_perms,
                                                email=m.project_member_with_perms.email,
                                                role__project=m.private_project1,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_member_without_perms,
                        email=m.project_member_without_perms.email,
                        role__project=m.private_project1,
                        role__permissions=[])

    m.private_membership2 = f.MembershipFactory(project=m.private_project2,
                                                user=m.project_member_with_perms,
                                                email=m.project_member_with_perms.email,
                                                role__project=m.private_project2,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project2,
                        user=m.project_member_without_perms,
                        email=m.project_member_without_perms.email,
                        role__project=m.private_project2,
                        role__permissions=[])

    f.MembershipFactory(project=m.public_project,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project2,
                        user=m.project_owner,
                        is_owner=True)

    m.public_issue_ca = f.IssueCustomAttributeFactory(project=m.public_project)
    m.private_issue_ca1 = f.IssueCustomAttributeFactory(project=m.private_project1)
    m.private_issue_ca2 = f.IssueCustomAttributeFactory(project=m.private_project2)

    #m.public_issue = f.IssueFactory(project=m.public_project, owner=m.project_owner)
    #m.private_issue1 = f.IssueFactory(project=m.private_project1, owner=m.project_owner)
    #m.private_issue2 = f.IssueFactory(project=m.private_project2, owner=m.project_owner)

    #m.public_issue_cav = f.IssueCustomAttributesValuesFactory(project=m.public_project,
    #                                                          issue=f.IssueFactory(project=m.public_project,
    #                                                                               owner=m.project_owner),
    #                                                          attributes_values={str(m.public_issue_ca.id):"test"})
    #m.private_issue_cav1 = f.IssueCustomAttributesValuesFactory(project=m.private_project1,
    #                                                            issue=f.IssueFactory(project=m.private_project1,
    #                                                                                 owner=m.project_owner),
    #                                                            attributes_values={str(m.private_issue_ca1.id):"test"})
    #m.private_issue_cav2 = f.IssueCustomAttributesValuesFactory(project=m.private_project2,
    #                                                            issue=f.IssueFactory(project=m.private_project2,
    #                                                                                 owner=m.project_owner),
    #                                                            attributes_values={str(m.private_issue_ca2.id):"test"})

    return m


#########################################################
# Issue Custom Attribute
#########################################################

def test_issue_custom_attribute_retrieve(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private1_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private2_url, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_issue_custom_attribute_create(client, data):
    public_url = reverse('issue-custom-attributes-list')
    private1_url = reverse('issue-custom-attributes-list')
    private2_url = reverse('issue-custom-attributes-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    issue_ca_data = {"name": "test-new", "project": data.public_project.id}
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'post', public_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 201]

    issue_ca_data = {"name": "test-new", "project": data.private_project1.id}
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'post', private1_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 201]

    issue_ca_data = {"name": "test-new", "project": data.private_project2.id}
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'post', private2_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 201]


def test_issue_custom_attribute_update(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    issue_ca_data = serializers.IssueCustomAttributeSerializer(data.public_issue_ca).data
    issue_ca_data["name"] = "test"
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'put', public_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_ca_data = serializers.IssueCustomAttributeSerializer(data.private_issue_ca1).data
    issue_ca_data["name"] = "test"
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'put', private1_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_ca_data = serializers.IssueCustomAttributeSerializer(data.private_issue_ca2).data
    issue_ca_data["name"] = "test"
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'put', private2_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 200]


def test_issue_custom_attribute_delete(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'delete', public_url, None, users)
    assert results == [401, 403, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private1_url, None, users)
    assert results == [401, 403, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private2_url, None, users)
    assert results == [401, 403, 403, 403, 204]


def test_issue_custom_attribute_list(client, data):
    url = reverse('issue-custom-attributes-list')

    response = client.json.get(url)
    assert len(response.data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.json.get(url)
    assert len(response.data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.json.get(url)
    assert len(response.data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.json.get(url)
    assert len(response.data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.json.get(url)
    assert len(response.data) == 3
    assert response.status_code == 200


def test_issue_custom_attribute_patch(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'patch', public_url, '{"name": "Test"}', users)
    assert results == [401, 403, 403, 403, 200]
    results = helper_test_http_method(client, 'patch', private1_url, '{"name": "Test"}', users)
    assert results == [401, 403, 403, 403, 200]
    results = helper_test_http_method(client, 'patch', private2_url, '{"name": "Test"}', users)
    assert results == [401, 403, 403, 403, 200]


def test_issue_custom_attribute_action_bulk_update_order(client, data):
    url = reverse('issue-custom-attributes-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_issue_custom_attributes": [(1,2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_custom_attributes": [(1,2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_custom_attributes": [(1,2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]


#########################################################
# Issue Custom Attributes Values
#########################################################

#def test_issue_custom_attributes_values_retrieve(client, data):
#    public_url = reverse('issue-custom-attributes-values-detail', args=[data.public_issue_cav.issue.id])
#    private1_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav1.issue.id])
#    private2_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav2.issue.id])
#    users = [
#        None,
#        data.registered_user,
#        data.project_member_without_perms,
#        data.project_member_with_perms,
#        data.project_owner
#    ]
#
#    results = helper_test_http_method(client, 'get', public_url, None, users)
#    assert results == [200, 200, 200, 200, 200]
#    results = helper_test_http_method(client, 'get', private1_url, None, users)
#    assert results == [200, 200, 200, 200, 200]
#    results = helper_test_http_method(client, 'get', private2_url, None, users)
#    assert results == [401, 403, 403, 200, 200]
#
#
#def test_issue_custom_attributes_values_update(client, data):
#    public_url = reverse('issue-custom-attributes-values-detail', args=[data.public_issue_cav.issue.id])
#    private1_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav1.issue.id])
#    private2_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav2.issue.id])
#
#    users = [
#        None,
#        data.registered_user,
#        data.project_member_without_perms,
#        data.project_member_with_perms,
#        data.project_owner
#    ]
#
#    issue_cav_data = serializers.IssueCustomAttributesValuesSerializer(data.public_issue_cav).data
#    issue_cav_data["values"] = '{{"{}":"test-update"}}'.format(data.public_issue_ca.id)
#    issue_cav_data = json.dumps(issue_cav_data)
#    results = helper_test_http_method(client, 'put', public_url, issue_cav_data, users)
#    assert results == [401, 403, 403, 403, 200]
#
#    issue_cav_data = serializers.IssueCustomAttributesValuesSerializer(data.private_issue_cav1).data
#    issue_cav_data["values"] = '{{"{}":"test-update"}}'.format(data.private_issue_ca1.id)
#    issue_cav_data = json.dumps(issue_cav_data)
#    results = helper_test_http_method(client, 'put', private1_url, issue_cav_data, users)
#    assert results == [401, 403, 403, 403, 200]
#
#    issue_cav_data = serializers.IssueCustomAttributesValuesSerializer(data.private_issue_cav2).data
#    issue_cav_data["values"] = '{{"{}":"test-update"}}'.format(data.private_issue_ca2.id)
#    issue_cav_data = json.dumps(issue_cav_data)
#    results = helper_test_http_method(client, 'put', private2_url, issue_cav_data, users)
#    assert results == [401, 403, 403, 403, 200]
#
#
#def test_issue_custom_attributes_values_delete(client, data):
#    public_url = reverse('issue-custom-attributes-values-detail', args=[data.public_issue_cav.issue.id])
#    private1_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav1.issue.id])
#    private2_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav2.issue.id])
#
#    users = [
#        None,
#        data.registered_user,
#        data.project_member_without_perms,
#        data.project_member_with_perms,
#        data.project_owner
#    ]
#
#    results = helper_test_http_method(client, 'delete', public_url, None, users)
#    assert results == [401, 403, 403, 403, 204]
#    results = helper_test_http_method(client, 'delete', private1_url, None, users)
#    assert results == [401, 403, 403, 403, 204]
#    results = helper_test_http_method(client, 'delete', private2_url, None, users)
#    assert results == [401, 403, 403, 403, 204]
#
#
#def test_issue_custom_attributes_values_list(client, data):
#    url = reverse('issue-custom-attributes-values-list')
#
#    response = client.json.get(url)
#    assert response.status_code == 404
#
#    client.login(data.registered_user)
#    response = client.json.get(url)
#    assert response.status_code == 404
#
#    client.login(data.project_member_without_perms)
#    response = client.json.get(url)
#    assert response.status_code == 404
#
#    client.login(data.project_member_with_perms)
#    response = client.json.get(url)
#    assert response.status_code == 404
#
#    client.login(data.project_owner)
#    response = client.json.get(url)
#    assert response.status_code == 404
#
#
#def test_issue_custom_attributes_values_patch(client, data):
#    public_url = reverse('issue-custom-attributes-values-detail', args=[data.public_issue_cav.issue.id])
#    private1_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav1.issue.id])
#    private2_url = reverse('issue-custom-attributes-values-detail', args=[data.private_issue_cav2.issue.id])
#
#    users = [
#        None,
#        data.registered_user,
#        data.project_member_without_perms,
#        data.project_member_with_perms,
#        data.project_owner
#    ]
#
#    results = helper_test_http_method(client, 'patch', public_url,
#                    '{{"values": {{"{}": "test-update"}}, "version": 1}}'.format(data.public_issue_ca.id), users)
#    assert results == [401, 403, 403, 403, 200]
#    results = helper_test_http_method(client, 'patch', private1_url,
#                    '{{"values": {{"{}": "test-update"}}, "version": 1}}'.format(data.private_issue_ca1.id), users)
#    assert results == [401, 403, 403, 403, 200]
#    results = helper_test_http_method(client, 'patch', private2_url,
#                    '{{"values": {{"{}": "test-update"}}, "version": 1}}'.format(data.private_issue_ca2.id), users)
#    assert results == [401, 403, 403, 403, 200]
