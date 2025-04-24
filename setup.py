from setuptools import setup

setup(
    name='galaxus',
    version='0.1',
    py_modules=['galaxus'],
    install_requires=[
        'click',
        'undetected-chromedriver',
        'webdriver-manager',
        'icecream',
        'selenium',
        'setuptools',
    ],
    entry_points='''
        [console_scripts]
        galaxus=galaxus:cli
    ''',
)
