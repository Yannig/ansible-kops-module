#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name,dangerous-default-value,duplicate-code

"""Retrieve information about defined kops cluster"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.kops import Kops, to_camel_case

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
     aliases: igName, ig-name
  image:
     description:
       - Image used to launch kube nodes (eg: kope.io/k8s-1.10-debian-jessie-amd64-hvm-ebs-2018-08-17)
     type: string
     required: False
     default: None
  machine_type:
     description:
       - Machine type used by nodes in instance group (eg: t2.medium)
     type: string
     required: False
     default: None
     aliases: machineType, machine-type
  min_size:
     description:
       - Min size of instance group (eg: 1). Default is 2.
     type: int
     required: False
     default: None
     aliases: minSize, min-size
  max_size:
     description:
       - Max size of instance group (eg: 5). Default is 5.
     type: int
     required: False
     default: None
     aliases: maxSize, max-size
  root_volume_size:
     description:
       - Root FS size (in Go). Default is 100.
     type: int
     required: False
     default: None
     aliases: rootVolumeSize, root-volume-size, node_size, node-size, nodeSize
  subnets:
     description:
       - Subnets used by instance group (eg: us-east-1a,us-east-1b)
     type: list
     required: False
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
{%- for option in ig_options %}
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
            ig_name=dict(type=str, required=True, aliases=['ig-name', 'igName']),
            state=dict(choices=['present', 'absent', 'started'], default='present'),
            image=dict(type=str, default=None),
            machine_type=dict(type=str, default=None, aliases=['machineType', 'machine-type']),
            max_size=dict(type=int, default=None, aliases=['maxSize', 'max-size']),
            min_size=dict(type=int, default=None, aliases=['minSize', 'min-size']),
            root_volume_size=dict(type=int, default=None, aliases=[
                'rootVolumeSize', 'root-volume-size', 'node_size', 'node-size', 'nodeSize'
            ]),
            subnets=dict(type=list, default=None),
{%- for option in ig_options %}
{{''}}            {{ option.name }}=dict(type={{ option.type|replace('list','str') }}{% if option.alias != option.name %}, aliases=['{{ option.alias }}']{% endif %}),
{%- endfor %}
        )
        # pylint: disable=line-too-long
        options_definition = {
{%- for option in ig_options %}
            '{{ option.name }}': {{ option }},
{%- endfor %}
        }
        super(KopsInstanceGroup, self).__init__(additional_module_args, options_definition)


    def update_ig(self, cluster_name, ig_name):
        """Update instance group"""
        ig_definition = self.get_nodes(cluster_name, ig_name)
        spec_to_merge = {}
        instance_group_parameters = [
            'image', 'machine_type', 'max_size', 'min_size', 'root_volume_size', 'subnets'
        ]
        for param in instance_group_parameters:
            value = self.module.params[param]
            if to_camel_case(param) in ig_definition['spec']:
                current_value = ig_definition['spec'][to_camel_case(param)]
            else:
                current_value = None

            if value is not None and value != current_value:
                spec_to_merge[to_camel_case(param)] = value

        return self.update_object_definition(cluster_name, ig_definition, spec_to_merge)


    def create_ig(self, cluster_name, ig_name):
        """Create instance group"""
        cmd = ["create", "instancegroup", "--edit=false", "--name", cluster_name, ig_name]

        (result, out, err) = self.run_command(cmd, add_optional_args_from_tag="create-ig")
        if result > 0:
            self.module.fail_json(msg=err, cmd=cmd)

        self.update_ig(cluster_name, ig_name)

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
        (result, out, err) = self.run_command(
            ["delete", "instancegroup", "--yes", "--name", cluster_name, ig_name]
        )
        if result > 0:
            self.module.fail_json(msg=err)
        return dict(
            changed=True,
            kops_output=out,
            cluster_name=cluster_name,
            ig_name=ig_name
        )


    def apply_present(self, cluster_name, ig_name, ig_exist, nodes_definition):
        """Create instance group or update it"""
        if ig_exist:
            changed = self.update_ig(cluster_name, ig_name)
            if changed:
                nodes_definition = self.get_nodes(cluster_name)

            if self.module.params['state'] == 'started':
                return self._apply_modifications(cluster_name)

            return dict(
                changed=changed,
                cluster_name=cluster_name,
                ig_name=ig_name,
                nodes_definition=nodes_definition[ig_name]
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

        self.module.fail_json(
            msg="Operation not supported",
            cluster_name=cluster_name,
            ig_name=ig_name
        )
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

