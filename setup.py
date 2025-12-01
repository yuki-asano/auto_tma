from setuptools import setup, find_packages


def _requires_from_file(filename):
    return open(filename).read().splitlines()


setup(
    name='auto_tma',
    version='0.1.0',
    description='',
    author='Yuki Asano',
    author_email='yuki.asano3206@gmail.com',
    packages=find_packages(),
    install_requires = _requires_from_file('requirements.txt')
)
