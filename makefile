kops_facts:
	ansible-playbook -M library -i localhost, tests/kops_facts.yml -vvv

tests: kops_facts
