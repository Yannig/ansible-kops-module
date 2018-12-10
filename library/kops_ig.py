#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name,dangerous-default-value,duplicate-code

"""Retrieve information about defined kops cluster"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.kops import Kops

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: kops_ig
short_description: Retrieve k8s cluster defined with kops
description:
     - Retrieve various informations of existing cluster defined using kops
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
  ig_name:
     description:
       - Instance group name.
     type: string
     required: true
  state:
     description:
       - If C(present), cluster will be created
       - If C(started), cluster will be created and check that the cluster is started
       - If C(absent), cluster will be deleted
     type: string
     required: false
     default: present
     choices: [ present, started, absent ]
  dry_run:
     description:
       - If true, only print the object that would be sent, without sending it. This flag can be used to create a cluster YAML or JSON manifest.
     type: bool
     required: false
     default: None
  role:
     description:
       - Type of instance group to create (Node,Master,Bastion)
     type: string
     required: false
     default: 'Node'
  subnet:
     description:
       - Subnet in which to create instance group. One of Availability Zone like eu-west-1a or a comma-separated list of multiple Availability Zones.
     type: list
     required: false
     default: None

notes:
   - kops bin is required
author:
   - Yannig Perré
'''

EXAMPLES = '''
- name: Retrieve kops cluster informations
  kops_ig:
'''

RETURN = '''
---
'''

class KopsInstanceGroup(Kops):
    """Handle instance group creation"""

    def __init__(self):
        """Init module parameters"""
        additional_module_args = dict(
            ig_name=dict(type=str, required=True, aliases=['ig-name']),
            state = dict(choices=['present', 'absent', 'started'], default='present'),
            dry_run = dict(type=bool, aliases=['dry-run']),
            role = dict(type=str),
            subnet = dict(type=str),
        )
        options_definition = {
            'dry_run': {'name': 'dry_run', 'alias': 'dry-run', 'type': 'bool', 'help': 'If true, only print the object that would be sent, without sending it. This flag can be used to create a cluster YAML or JSON manifest.', 'default': None, 'tag': 'create-ig'},
            'role': {'name': 'role', 'alias': 'role', 'type': 'str', 'help': 'Type of instance group to create (Node,Master,Bastion)', 'default': "'Node'", 'tag': 'create-ig'},
            'subnet': {'name': 'subnet', 'alias': 'subnet', 'type': 'list', 'help': 'Subnet in which to create instance group. One of Availability Zone like eu-west-1a or a comma-separated list of multiple Availability Zones.', 'default': None, 'tag': 'create-ig'},
        }
        super(KopsInstanceGroup, self).__init__(additional_module_args, options_definition)


    def create_ig(self, cluster_name, ig_name):
        """Create instance group"""
        cmd = ["create", "instancegroup", "--edit=false", "--name", cluster_name, ig_name]

        (result, out, err) = self.run_command(cmd, add_optional_args_from_tag="create-ig")
        if result > 0:
            self.module.fail_json(msg=err, cmd=cmd)

        if self.module.params['state'] == 'started':
            return self._apply_modifications(cluster_name)

        return dict(
            changed=True,
            cluster_name=cluster_name,
            ig_name=ig_name,
            kops_output=out
        )


    def delete_ig(self, cluster_name, ig_name):
        """Delete instance group"""
        (result, out, err) = self.run_command(["delete", "instancegroup", "--yes", "--name", cluster_name, ig_name])
        if result > 0:
            self.module.fail_json(msg=err)
        return dict(
            changed=True,
            kops_output=out,
            cluster_name=cluster_name,
            ig_name=ig_name
        )


    def apply_present(self, cluster_name, ig_name, ig_exist, nodes_definition):
        if ig_exist:
            if self.module.params['state'] == 'started':
                return self._apply_modifications(cluster_name)

            return dict(
                changed=False,
                cluster_name=cluster_name,
                ig_name=ig_name,
                nodes_definition=nodes_definition
            )
        return self.create_ig(cluster_name, ig_name)

    def apply_absent(self, cluster_name, ig_name, ig_exist):
        """Delete nodes if instance group exist"""
        if not ig_exist:
            return dict(
                changed=False,
                cluster_name=cluster_name,
                ig_name=ig_name,
            )
        return self.delete_ig(cluster_name, ig_name)


    def check_ig_state(self, ig_name):
        """Check instance group state"""
        cluster_name = self.module.params['name']
        state = self.module.params['state']
        nodes_definition = self.get_nodes(cluster_name=cluster_name)
        ig_exist = ig_name in nodes_definition

        if state in ['present', 'started']:
            return self.apply_present(cluster_name, ig_name, ig_exist, nodes_definition)

        if state == 'absent':
            return self.apply_absent(cluster_name, ig_name, ig_exist)

        self.module.fail_json(msg="Operation not supported", cluster_name=cluster_name, ig_name=ig_name)
        return None

    def exit_json(self):
        """Send back result to Ansible"""
        results = self.check_ig_state(self.module.params['ig_name'])

        self.module.exit_json(**results)


def main():
    """Start facts gathering"""
    facts = KopsInstanceGroup()
    facts.exit_json()


if __name__ == '__main__':
    main()