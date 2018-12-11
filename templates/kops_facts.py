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
module: kops_facts
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
  failed_when_not_found:
     description:
       - Module will crash if cluster doesn't exist. No crash by default.
     type: bool
     required: false
     default: false
  full:
     description:
       - Show fully populated configuration from kops.
     type: bool
     required: false
     default: false

notes:
   - kops bin is required
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

class KopsFacts(Kops):
    """Retrieve facts from existing cluster"""

    def __init__(self):
        """Init module parameters"""
        additional_module_args = dict(
            failed_when_not_found=dict(type=bool, default=False),
            full=dict(type=bool, default=False),
        )
        super(KopsFacts, self).__init__(additional_module_args=additional_module_args)

    def get_facts(self):
        """Retrieve clusters definition"""
        clusters_definitions = self.get_clusters(
            self.module.params['name'],
            failed_when_not_found=self.module.params['failed_when_not_found'],
            full=self.module.params['full']
        )

        return dict(
            kops_path=self.kops_cmd,
            kops_clusters=clusters_definitions.keys(),
            kops_clusters_definitions=clusters_definitions,
        )


    def exit_json(self):
        """Send back result to Ansible"""
        results = dict(
            changed=False,
            ansible_facts=self.get_facts()
        )

        self.module.exit_json(**results)


def main():
    """Start facts gathering"""
    facts = KopsFacts()
    facts.exit_json()


if __name__ == '__main__':
    main()

