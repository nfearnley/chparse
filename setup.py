from setuptools import setup
import re

with open('chparse\\__init__.py') as f:
    content = f.read()
    longdesc = re.match(r'^"""([\s\S]+?)"""', content).group(1).strip()
    version = re.search(r'__version__\s*=\s*"([^"]+)"', content).group(1)
del f, content

setup(
    name="chparse",
    version=version,
    description="Parse Clone Hero charts with ease!.",
    long_description=longdesc,
    url="https://github.com/Kenny2github/chparse",
    author="Ken Hilton",
    license="GPLv3+",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Text Processing :: Markup',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    keywords='file format parser',
    packages=['chparse'],
    python_requires='>=3.6',
    test_suite='nose.collector',
    tests_require=['nose'],
)
