pip install twine
python setup.py sdist bdist_wheel
twine upload -r pypi dist/*