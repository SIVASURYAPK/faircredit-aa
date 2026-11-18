# conftest.py — placed at the project root.
# pytest automatically loads this file, and having it here tells pytest
# (and Python) to treat the project root as the base for imports.
# This means `from features.build_features import ...` works in all test files
# without any sys.path hacks.
