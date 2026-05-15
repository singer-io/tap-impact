#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='tap-impact',
      version='2.2.0',
      description='Singer.io tap for extracting data from the Impact Advertiser, Partner, Agency APIs',
      author='jeff.huth@bytecode.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_impact'],
      install_requires=[
          'backoff==2.2.1',
          'requests==2.33.0',
          'singer-python==6.8.0'
      ],
      extras_require={
          'dev': [
              'ipdb',
              'pylint',
              'pytest',
              'parameterized'
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
