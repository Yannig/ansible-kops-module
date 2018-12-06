#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: kops_facts
short_description: Handle cluster create by kops
description:
     - Blabla
     - Blabla
version_added: "2.8"
options:
  to_be_defined:
     description:
       - description
     type: string
     required: false
     default: false
notes:
   - blabla
author:
    - Yannig Perré
'''

EXAMPLES = '''
- name: Retrieve kops cluster informations
  kops_facts:
'''

RETURN = '''
---
'''

import re, yaml

class kops_facts():

    module = None
    kops_cmd = None
    kops_cluster = []
    kops_args = []

    def __init__(self):
        self.module = AnsibleModule(
            argument_spec=dict(
                state_store=dict(type='str'),
                name=dict(type='str'),
                kops_cmd=dict(type='str'),
            ),
        )
        self._detect_kops_cmd()


    def _detect_kops_cmd(self):
        self.kops_cmd = self.module.params['kops_cmd']
        if self.kops_cmd is None:
            self.kops_cmd = self.module.get_bin_path('kops')

        if self.kops_cmd is None:
            self.module.fail_json(msg="Unable to locate kops binary")

        if self.module.params['state_store'] is not None:
            self.kops_args += [ '--state', self.module.params['state_store'] ]


    def run_command(self, options):
        return self.module.run_command([self.kops_cmd ] + self.kops_args + options)


    def get_cluster_definition(self, cluster_name):
        (rc, out, err) = self.run_command([ "get", "cluster", cluster_name, "-o=yaml"])
        if rc > 0:
            self.module.fail_json(msg=err.strip())
        return yaml.load(out)

    def get_clusters(self, name = None):
        cmd = [ "get", "clusters"]
        if name is not None:
            cmd += [ "--name", name ]

        (rc, out, err) = self.run_command(cmd)
        if rc > 0:
            self.module.fail_json(msg=err.strip())
        clusters = []
        skip_first_line = True
        for line in out.split("\n"):
            if skip_first_line:
                skip_first_line = False
                continue
            cluster_name = line.split("\t")[0]
            if len(cluster_name) > 0:
                clusters.append(cluster_name)
        return clusters


    def get_facts(self):
        self.kops_cluster = self.get_clusters()
        clusters = self.get_clusters(self.module.params['name'])
        clusters_definition = {}
        for cluster_name in clusters:
            clusters_definition[cluster_name] = self.get_cluster_definition(cluster_name)

        return dict(
            kops_path=self.kops_cmd,
            kops_clusters=clusters,
            kops_clusters_definitions=clusters_definition,
        )


    def exit_json(self):
        results = dict(
            changed=False,
            ansible_facts=self.get_facts()
        )

        self.module.exit_json(**results)

def main():

    facts = kops_facts()
    facts.exit_json()

if __name__ == '__main__':
    main()
