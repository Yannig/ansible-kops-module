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

class KopsCluster(Kops):
    """Handle state for kops cluster"""

    def __init__(self):
        """Init module parameters"""
        addition_module_args = dict(
            state=dict(choices=['present', 'absent', 'stopped', 'started'], default='present')
        )
        super(KopsCluster, self).__init__(addition_module_args=addition_module_args)


    def check_cluster_state(self):
        """Check cluster state and apply expected state"""
        cluster_name = self.module.params['name']
        state = self.module.params['state']
        defined_clusters = self.get_clusters(
            name=cluster_name,
            retrieve_ig=False,
            failed_when_not_found=False
        )

        if state == 'present' and cluster_name in defined_clusters:
            return dict(
                changed=False,
                cluster_name=cluster_name,
                defined_clusters=defined_clusters
            )

        if state == 'stopped' and cluster_name in defined_clusters:
            return dict(
                changed=False,
                cluster_name=cluster_name,
                defined_clusters=defined_clusters
            )

        self.module.fail_json(msg="Operation not supported")
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
