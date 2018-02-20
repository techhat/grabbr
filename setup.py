#!/usr/bin/env python

from setuptools import setup


setup(
    name='grabbr',
    version='0.6.3',
    description='Data mining tool',
    author='Joseph Hall',
    author_email='techhat@gmail.com',
    url='https://github.com/techhat/grabbr',
    packages=['grabbr'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    install_requires=[
        'beautifulsoup4',
        'psycopg2',
        'pyyaml',
        'requests',
        'termcolor',
    ],
    scripts=['scripts/grabbr'],
    data_files=[
        ('share/grabbr', ['schema/grabbr.sql']),
    ],
)
