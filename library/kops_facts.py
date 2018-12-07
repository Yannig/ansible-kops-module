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

class KopsFacts(Kops):
    """Retrieve facts from existing cluster"""

    def __init__(self):
        """Init module parameters"""
        addition_module_args = dict(
            failed_when_not_found=dict(type=bool, default=False),
        )
        super(KopsFacts, self).__init__(addition_module_args=addition_module_args)

    def get_facts(self):
        """Retrieve clusters definition"""
        clusters_definitions = self.get_clusters(self.module.params['name'], failed_when_not_found=self.module.params['failed_when_not_found'])

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
