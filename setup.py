from setuptools import setup, find_packages

setup(
    name='WebGUI',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'PyYAML~=5.4.1',
        'tornado~=6.33',
        'setuptools~=68.2.0',
        'viswaternet~=1.1.0',
        'matplotilib~=3.5.0'
    ],
    entry_points={
        'console_scripts': [
            'webgui = main_entry:run_server',
        ],
    },
)
