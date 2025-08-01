#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='tap-impact',
      version='2.1.2',
      description='Singer.io tap for extracting data from the Impact Advertiser, Partner, Agency APIs',
      author='jeff.huth@bytecode.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_impact'],
      install_requires=[
          'backoff==1.10.0',
          'requests==2.32.4',
          'singer-python==5.13.2'
      ],
      extras_require={
          'dev': [
              'ipdb',
              'pylint==2.5.3'
          ]
      },
      entry_points='''
          [console_scripts]
          tap-impact=tap_impact:main
      ''',
      packages=find_packages(),
      package_data={
          'tap_impact': [
              'schemas/*.json'
          ]
      })
