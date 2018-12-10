#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os,re
from jinja2 import Environment, FileSystemLoader

path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.join(path, '../library')
modules_output = os.path.join(path, '../generated-modules')

env = Environment(loader = FileSystemLoader(modules_path))

option_to_ignore = ["yes", "help", "interactive"]

def get_ansible_type(option_type):
    if option_type is None: return 'bool'
    if option_type == 'strings': return 'list'
    if option_type == 'string': return 'str'
    if option_type == 'int32': return 'int'
    return 'str'


def load_help(cmd, tag):
    output = os.popen(cmd).read().split("\n")
    while len(output) > 0:
        current_line = output.pop(0)
        if current_line == 'Flags:':
            break

    kops_options = []

    for line in output:
        if line == 'Global Flags:': break
        match = re.search('^\s+(\-(\w),)?\s*(\-\-(\S+))(\s(\w+))?\s+(.+)$', line)
        if match:
            alias = match.group(4)
            option = alias.replace('-', '_')
            if option in option_to_ignore: continue

            option_type = match.group(6)

            option_help = match.group(7)
            match = re.search('^(.*)\s*\(default (.*)\)$', option_help)
            option_default = None
            if match:
                option_help = match.group(1)
                option_default = match.group(2)

            option_type = get_ansible_type(option_type)
            if option_default != None:
                option_default = option_default.replace('"', '')
                option_default = "'%s'" % option_default

            kops_options.append(
                dict(
                    name = option,
                    alias = alias,
                    type = option_type,
                    help = option_help,
                    default = option_default,
                    tag = tag
                )
            )

    return kops_options

cluster_options = load_help("kops create cluster --help", "create")
rolling_update_options = load_help("kops rolling-update cluster --help", "rolling-update")

for module in ['kops_cluster.py', 'kops_facts.py']:
    module_template = env.get_template(module)

    with open(modules_output + '/' + module, 'w') as f:
        rendered_module = module_template.render(
            dict(
                cluster_options=cluster_options,
                rolling_update_options=rolling_update_options,
            )
        )
        f.write(rendered_module)
