#!/usr/bin/env python

from setuptools import setup


setup(
    name='webflayer',
    version='0.6.5',
    description='Data mining tool',
    author='Joseph Hall',
    author_email='techhat@gmail.com',
    url='https://github.com/techhat/webflayer',
    packages=['webflayer'],
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
    scripts=['scripts/flay'],
    data_files=[
        ('share/webflayer', ['schema/webflayer.sql']),
    ],
)
