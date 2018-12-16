#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name,dangerous-default-value,duplicate-code

"""Handle kops cluster creation/deletion"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.kops import Kops, to_camel_case

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: kops_cluster
short_description: Handle cluster creation with kops
description:
     - Let you create or delete cluster using kops
version_added: "2.8"
options:
  name:
     description:
       - FQDN name of the cluster (eg: test.example.org)
     type: string
     required: true
  state_store:
     description:
       - State store (eg: s3://my-state-store)
     type: string
     required: false
     default: None
  kops_cmd:
     description:
       - kops bin path
     type: string
     required: false
     default: None
  state:
     description:
       - If C(present), cluster will be created
       - If C(updated), cluster will be created and check that the cluster is updated
       - If C(absent), cluster will be deleted
     type: string
     required: false
     default: present
     choices: [ present, updated, absent ]
  additional_policies:
     description:
       - Additional policies for nodes in kops cluster
     type: dict
     required: false
     default: None
  docker:
     description:
       - Docker configuration
     type: dict
     required: false
     default: None
{%- for option in cluster_options + rolling_update_options %}
  {{ option.name }}:
     description:
       - {{ option.help|replace('--', '') }}
     type: {{ option.type|replace('str', 'string') }}
     required: false
     default: {{ option.default }}
{%- endfor %}
notes:
   - kops bin is required
author:
   - Yannig Perré
'''

EXAMPLES = '''
- name: Create kube cluster with kops
  kops_cluster:
    name: test
    state: present
'''

RETURN = '''
---
'''

class KopsCluster(Kops):
    """Handle state for kops cluster"""

    SPECIAL_CASE = {
        "admin_access": {
            "field": "kubernetesApiAccess",
            "transform": "list"
        },
        "ssh_access": {
            "transform": "list"
        }
    }

    def __init__(self):
        """Init module parameters"""
        additional_module_args = dict(
            state=dict(choices=['present', 'absent', 'updated'], default='present'),
            cloud=dict(choices=['gce', 'aws', 'vsphere'], default='aws'),
            docker=dict(type=dict),
            additional_policies=dict(type=dict, aliases=['additional-policies', 'additionalPolicies']),
{%- for option in cluster_options + rolling_update_options %}
{%    if option.name not in ['cloud'] -%}
{{''}}            {{ option.name }}=dict(type={{ option.type|replace('list','str') }}{% if option.alias != option.name %}, aliases=['{{ option.alias }}']{% endif %}),
{%-    endif %}
{%- endfor %}
        )
        # pylint: disable=line-too-long
        options_definition = {
{%- for option in cluster_options + rolling_update_options %}
            '{{ option.name }}': {{ option }},
{%- endfor %}
        }
        super(KopsCluster, self).__init__(additional_module_args, options_definition)


    def delete_cluster(self, cluster_name):
        """Delete cluster"""
        (result, out, err) = self.run_command(
            ["delete", "cluster", "--yes", "--name", cluster_name]
        )
        if result > 0:
            self.module.fail_json(msg=err)
        return dict(
            changed=True,
            kops_output=out,
            cluster_name=cluster_name,
        )


    def create_cluster(self, cluster_name):
        """Create cluster using kops"""
        cmd = ["create", "cluster", "--name", cluster_name]

        if self.module.params['state'] in ['updated', 'started']:
            cmd.append("--yes")

        (result, out, err) = self.run_command(cmd, add_optional_args_from_tag="create")
        if result > 0:
            self.module.fail_json(msg=err)

        # Handle docker definition (version, options)
        self.update_cluster(cluster_name)

        return dict(
            changed=True,
            cluster_name=cluster_name,
            kops_output=out
        )


    def get_spec_name(self, param):
        """
          Send back variable name as expected in spec field from param name
          Handle corner case like Cidr/CIDR or special case
        """
        if param in self.SPECIAL_CASE and self.SPECIAL_CASE[param].get('field'):
            return self.SPECIAL_CASE[param]['field']

        return to_camel_case(param).replace('Cidr', 'CIDR')

    def convert_value(self, param, value):
        """Do some transformation from string to list using SPECIAL_CASE values"""
        if param in self.SPECIAL_CASE:
            if self.SPECIAL_CASE[param]['transform'] == 'list':
                return [x.strip() for x in value.split(",")]
        # If not a special case, send unchanged value
        return value

    def update_cluster(self, cluster_name):
        """Update cluster"""
        cluster_definition = self.get_clusters(cluster_name)

        spec_to_merge = {}
        cluster_parameters = [
            'kubernetes_version', 'master_public_name', 'network_cidr',
            'admin_access', 'ssh_access', 'docker', 'additional_policies',
        ]
        for param in cluster_parameters:
            spec_name = self.get_spec_name(param)
            value = self.module.params[param]
            if spec_name in cluster_definition['spec']:
                current_value = cluster_definition['spec'][spec_name]
            else:
                current_value = None

            if value is not None and value != current_value:
                spec_to_merge[spec_name] = value

        return self.update_object_definition(cluster_name, cluster_definition, spec_to_merge)


    def apply_present(self, cluster_name, defined_cluster):
        """Create cluster if does not exist"""
        if defined_cluster:
            changed = self.update_cluster(cluster_name)
            if self.module.params['state'] in ['updated', 'started']:
                return self._apply_modifications(cluster_name)
            if changed:
                defined_cluster = self.get_clusters(cluster_name)
            return dict(
                changed=changed,
                cluster_name=cluster_name,
                defined_cluster=defined_cluster
            )
        return self.create_cluster(cluster_name)


    def apply_absent(self, cluster_name, cluster_exist):
        """Delete cluster if cluster exist"""
        if not cluster_exist:
            return dict(
                changed=False,
                cluster_name=cluster_name,
            )
        return self.delete_cluster(cluster_name)


    def check_cluster_state(self):
        """Check cluster state and apply expected state"""
        cluster_name = self.module.params['name']
        state = self.module.params['state']
        defined_cluster = self.get_clusters(
            cluster_name=cluster_name,
            retrieve_ig=False,
            failed_when_not_found=False
        )

        if state in ['present', 'updated']:
            return self.apply_present(cluster_name, defined_cluster)

        if state == 'absent':
            return self.apply_absent(cluster_name, defined_cluster)

        self.module.fail_json(msg="Operation not supported", defined_cluster=defined_cluster)
        return None


    def exit_json(self):
        """Send back result to Ansible"""
        results = self.check_cluster_state()

        self.module.exit_json(**results)


def main():
    """Kops cluster handling"""
    cluster = KopsCluster()
    cluster.exit_json()


if __name__ == '__main__':
    main()

