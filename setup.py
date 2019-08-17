from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name='line',
    version='1.0',
    description='Creating nice line plot with least typing',
    author='Yanze Wu',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        'numpy >= 1.13.0',
        'pandas >= 0.22.0',
        'matplotlib >= 3.0.0',
        'pyqt5 >= 5.0'
    ],
    entry_points = {
        'console_scripts': [
            'line = line.__main__:main',
        ],
    },
)