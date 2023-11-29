del /q .\dist
del /q .\build
pip install twine
python -m build
twine upload -r pypi dist/*
del /q .\dist
del /q .\build