#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import yaml

class Kops():

    module = None
    kops_cmd = None
    kops_cluster = []
    kops_args = []
    default_module_args = dict(
        state_store=dict(type='str'),
        name=dict(type='str'),
        kops_cmd=dict(type='str'),
    )

    def __init__(self, addition_module_args=dict()):
        self.module = AnsibleModule(
          argument_spec=dict(
            self.default_module_args,
            **addition_module_args
          )
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


    def get_nodes(self, cluster_name):
        cmd = [ "get", "instancegroups", "--name", cluster_name ]

        (rc, out, err) = self.run_command(cmd + [ "-o=yaml" ])
        if rc > 0:
            self.module.fail_json(msg=err.strip())

        nodes_definitions = {}
        for ig in out.split("---\n"):
            definition = yaml.load(ig)
            name = definition['metadata']['name']
            nodes_definitions[name] = definition

        return nodes_definitions

        return cluster_definition

    def get_clusters(self, name=None, retrieve_ig=True, failed_when_not_found=True):
        cmd = [ "get", "clusters"]
        if name is not None:
            cmd += [ "--name", name ]

        (rc, out, err) = self.run_command(cmd + [ "-o=yaml" ])
        if rc > 0:
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


