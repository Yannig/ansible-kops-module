kops_facts:
	ANSIBLE_MODULE_UTILS=./module_utils ansible-playbook -M library -i localhost, tests/kops_facts.yml -vvv

kops_cluster:
	ANSIBLE_MODULE_UTILS=./module_utils ansible-playbook -M library -i localhost, tests/kops_cluster.yml -vvv

pylint:
	PYTHONPATH=. pylint --disable R0801,E0401,E0611 module_utils/kops.py library/kops_*.py

tests: kops_facts kops_cluster
