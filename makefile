CLUSTER_NAME            = test
ANSIBLE_OPTIONS        ?=
ANSIBLE_COMMON_OPTIONS ?=-M library -i localhost,
ANSIBLE_CMD             = ansible-playbook $(ANSIBLE_COMMON_OPTIONS) $(ANSIBLE_OPTIONS)

render-modules:
	./helper/generate-module.py

kops_facts: render-modules
	ANSIBLE_MODULE_UTILS=./module_utils $(ANSIBLE_CMD) tests/kops_facts.yml -e cluster_name=$(CLUSTER_NAME)

kops_cluster: render-modules
	ANSIBLE_MODULE_UTILS=./module_utils $(ANSIBLE_CMD) tests/kops_cluster.yml -e cluster_name=$(CLUSTER_NAME)

kops_ig: render-modules
	ANSIBLE_MODULE_UTILS=./module_utils $(ANSIBLE_CMD) tests/kops_ig.yml -e cluster_name=$(CLUSTER_NAME)

pylint:
	PYTHONPATH=. pylint --disable R0801,E0401,E0611 module_utils/kops.py library/kops_*.py

tests: pylint kops_facts kops_cluster kops_ig
