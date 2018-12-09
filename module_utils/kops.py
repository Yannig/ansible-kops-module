#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name,dangerous-default-value,duplicate-code

"""This class handle kops communication for Kops Ansible modules"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
import yaml

class Kops():
    """handle kops communication by detecting kops bin path and setting kops options"""

    module = None
    kops_cmd = None
    kops_cluster = []
    kops_args = []
    default_module_args = dict(
        state_store=dict(type='str'),
        name=dict(type='str'),
        kops_cmd=dict(type='str'),
    )
    optional_module_args = None
    options_definition = {}

    def __init__(self, addition_module_args=None, options_definition=None):
        """Init Ansible module options"""
        if addition_module_args is not None:
            self.addition_module_args = addition_module_args

        self.module = AnsibleModule(
            argument_spec=dict(
                self.default_module_args,
                **addition_module_args
            )
        )
        if options_definition is not None:
            self.options_definition = options_definition
        self._detect_kops_cmd()


    def _detect_kops_cmd(self):
        """Find where is stored kops binary"""
        self.kops_cmd = self.module.params['kops_cmd']
        if self.kops_cmd is None:
            self.kops_cmd = self.module.get_bin_path('kops')

        if self.kops_cmd is None:
            self.module.fail_json(msg="Unable to locate kops binary")

        if self.module.params['state_store'] is not None:
            self.kops_args += ['--state', self.module.params['state_store']]

        # Construct command to launch using options definition
        for k, v in iteritems(self.options_definition):
            if self.module.params[k] is None: continue
            if v['type'] == 'bool':
                self.kops_args += ['--' + v['alias']]
            else:
                self.kops_args += ['--' + v['alias'], self.module.params[k]]

    def run_command(self, options):
        """Run kops using kops arguments"""
        try:
            return self.module.run_command([self.kops_cmd] + self.kops_args + options)
        except:
            self.module.fail_json(
                msg="error while launching kops",
                kops_cmd=self.kops_cmd,
                kops_args=self.kops_args,
                kops_options=options,
            )


    def get_nodes(self, cluster_name):
        """Retrieve instance groups (nodes, master)"""
        cmd = ["get", "instancegroups", "--name", cluster_name]

        (result, out, err) = self.run_command(cmd + ["-o=yaml"])
        if result > 0:
            self.module.fail_json(msg=err.strip())

        nodes_definitions = {}
        for istance_group in out.split("---\n"):
            definition = yaml.load(istance_group)
            name = definition['metadata']['name']
            nodes_definitions[name] = definition

        return nodes_definitions


    def get_clusters(self, name=None, retrieve_ig=True, failed_when_not_found=True):
        """Retrieve defined clusters"""
        cmd = ["get", "clusters"]
        if name is not None:
            cmd += ["--name", name]

        (result, out, err) = self.run_command(cmd + ["-o=yaml"])
        if result > 0:
            if not failed_when_not_found and name is not None:
                return {}
            self.module.fail_json(msg=err.strip())

        clusters_definitions = {}
        for cluster in out.split("---\n"):
            cluster_definition = yaml.load(cluster)
            cluster_name = cluster_definition['metadata']['name']
            if retrieve_ig:
                cluster_definition["instancegroups"] = self.get_nodes(cluster_name)
            clusters_definitions[cluster_name] = cluster_definition
        return clusters_definitions
