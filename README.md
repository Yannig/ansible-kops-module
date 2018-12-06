# ansible-kops-module

Kops modules for Ansible

## Goals

This modules let you create kubernetes cluster using **kops** command using declaration.

I use mainly this module to create cluster with AWS.

## How to use it

You can have a look at the tests directory. There's a couple of playbooks that show you how to use them.

You can use the same variable as with kops/aws to handle communication with kops cluster (ie **KOPS_STATE_STORE**, **AWS_ACCESS_KEY_ID** and **AWS_ACCESS_ACCESS_KEY**).

Feedbacks are welcome.

Here an example to retrieve facts from cluster **test**:

```shell
export AWS_ACCESS_KEY_ID=xxx
export AWS_ACCESS_ACCESS_KEY=xxxxxxxxxxx
export KOPS_STATE_STORE=s3://my-state-store-in-s3
```

    $ ansible -M ./library -m kops_facts localhost

Truncated output:

```json
localhost | SUCCESS => {
    "ansible_facts": {
        "kops_clusters": [
            "test.fqdn"
        ],
        "kops_clusters_definitions": {
            "test.fqdn": {
                "apiVersion": "kops/v1alpha2",
                "kind": "Cluster",
                "metadata": {
                    "creationTimestamp": "2018-12-03T10:42:44",
                    "name": "test.fqdn"
                },
[...]
```
