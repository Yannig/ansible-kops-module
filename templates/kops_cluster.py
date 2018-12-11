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
       - If C(started), cluster will be created and check that the cluster is started
       - If C(absent), cluster will be deleted
     type: string
     required: false
     default: present
     choices: [ present, started, absent ]
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

    def __init__(self):
        """Init module parameters"""
        additional_module_args = dict(
            state=dict(choices=['present', 'absent', 'started'], default='present'),
            cloud=dict(choices=['gce', 'aws', 'vsphere'], default='aws'),
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

        if self.module.params['state'] == 'started':
            cmd.append("--yes")

        (result, out, err) = self.run_command(cmd, add_optional_args_from_tag="create")
        if result > 0:
            self.module.fail_json(msg=err)
        return dict(
            changed=True,
            cluster_name=cluster_name,
            kops_output=out
        )


    def update_cluster(self, cluster_name):
        """Update cluster"""
        cluster_definition = self.get_clusters(cluster_name)

        spec_to_merge = {}
        for param in ['kubernetes_version', 'master_public_name']:
            value = self.module.params[param]
            if to_camel_case(param) in cluster_definition['spec']:
                current_value = cluster_definition['spec'][to_camel_case(param)]
            else:
                current_value = None

            if value is not None and value != current_value:
                spec_to_merge[to_camel_case(param)] = value

        return self.update_object_definition(cluster_name, cluster_definition, spec_to_merge)


    def apply_present(self, cluster_name, defined_cluster):
        """Create cluster if does not exist"""
        if defined_cluster:
            changed = self.update_cluster(cluster_name)
            if self.module.params['state'] == 'started':
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

        if state in ['present', 'started']:
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

