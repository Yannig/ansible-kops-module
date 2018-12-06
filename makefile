kops_facts:
	ANSIBLE_MODULE_UTILS=./module_utils ansible-playbook -M library -i localhost, tests/kops_facts.yml -vvv

kops_cluster:
	ANSIBLE_MODULE_UTILS=./module_utils ansible-playbook -M library -i localhost, tests/kops_cluster.yml -vvv

tests: kops_facts kops_cluster
