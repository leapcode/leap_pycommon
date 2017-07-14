.PHONY: upload
default:
	# doing nothing. try 'make upload'
upload:
	python setup.py sdist bdist_wheel --universal upload  --sign -i kali@leap.se -r pypi
