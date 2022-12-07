rm -rf build/*
rm -rf dist/*
pip install twine
python setup.py sdist bdist_wheel
twine upload -r pypi dist/*
rm -rf build/*
rm -rf dist/*