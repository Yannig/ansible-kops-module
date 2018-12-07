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
module: kops_cluster
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
- name: Create kube cluster with kops
  kops_cluster:
    name: test
    state: present
'''

RETURN = '''
---
'''

from ansible.module_utils.kops import Kops

class KopsCluster(Kops):

    def __init__(self):
        addition_module_args = dict(
          state=dict(choices=['present', 'absent', 'stopped', 'started'], default='present')
        )
        super(KopsCluster, self).__init__(addition_module_args=addition_module_args)

    def check_cluster_state(self):

        cluster_name = self.module.params['name']
        state = self.module.params['state']
        defined_clusters = self.get_clusters(name=cluster_name, retrieve_ig=False, failed_when_not_found=False)

        if state == 'present' and cluster_name in defined_clusters:
            self.module.exit_json(changed=False)

        if state == 'stopped' and cluster_name in defined_clusters:
            self.module.exit_json(changed=False)

    def exit_json(self):
        self.check_cluster_state()
        results = dict(
            changed=False,
        )

        self.module.exit_json(**results)

def main():
    cluster = KopsCluster()
    cluster.exit_json()

if __name__ == '__main__':
    main()
