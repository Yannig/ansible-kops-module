#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name,dangerous-default-value,duplicate-code

"""Handle kops cluster creation/deletion"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.kops import Kops

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
     default: None
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
        addition_module_args = dict(
            state = dict(choices=['present', 'absent', 'started'], default='present'),
            cloud = dict(choices=['gce', 'aws', 'vsphere'], default='aws'),
{%- for option in cluster_options + rolling_update_options %}
{%    if option.name not in ['cloud'] -%}
{{''}}            {{ option.name }} = dict(type={{ option.type|replace('list','str') }}{% if option.alias != option.name %}, aliases=['{{ option.alias }}']{% endif %}),
{%-    endif %}
{%- endfor %}
        )
        options_definition = {
{%- for option in cluster_options %}
            '{{ option.name }}': {{ option }},
{%- endfor %}
        }
        super(KopsCluster, self).__init__(addition_module_args, options_definition)

    def delete_cluster(self, cluster_name):
        """Delete cluster"""
        (result, out, err) = self.run_command(["delete", "cluster", "--yes", "--name", cluster_name])
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

        (result, out, err) = self.run_command(cmd, add_optional_args=True)
        if result > 0:
            self.module.fail_json(msg=err)
        return dict(
            changed=True,
            cluster_name=cluster_name,
            kops_output=out
        )


    def apply_present(self, cluster_name, cluster_exist, defined_clusters):
        """Create cluster if does not exist"""
        if cluster_exist:
            if self.module.params['state'] == 'started':

                cmd = ["update", "cluster", cluster_name, "--yes"]
                (result, update_output, update_operations) = self.run_command(cmd)
                if result > 0:
                    self.module.fail_json(msg=err)

                cmd = ["rolling-update", "cluster", cluster_name, "--cloudonly"]
                (result, out, err) = self.run_command(cmd)
                if result > 0:
                    self.module.fail_json(msg=err)
                changed = "No rolling-update required." not in out

                if changed:
                    cmd = ["rolling-update", "cluster", cluster_name, "--yes"]
                    if self.module.params['cloudonly']:
                        cmd += ["--cloudonly"]

                    (result, out, err) = self.run_command(cmd)
                    if result > 0:
                        self.module.fail_json(msg=err)

                return dict(
                    changed=changed,
                    cluster_name=cluster_name,
                    update_operations=update_operations,
                    update_output=update_output,
                    rolling_update_output=out,
                    rolling_update_operations=err,
                )
            return dict(
                changed=False,
                cluster_name=cluster_name,
                defined_clusters=defined_clusters
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
        defined_clusters = self.get_clusters(
            name=cluster_name,
            retrieve_ig=False,
            failed_when_not_found=False
        )
        cluster_exist = defined_clusters.get(cluster_name) is not None

        if state in ['present', 'started']:
            return self.apply_present(cluster_name, cluster_exist, defined_clusters)

        if state == 'absent':
            return self.apply_absent(cluster_name, cluster_exist)

        self.module.fail_json(msg="Operation not supported", defined_clusters=defined_clusters)
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
