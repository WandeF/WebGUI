from setuptools import setup, find_packages

setup(
    name='WebGUI',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'tornado',
    ],
    entry_points={
        'console_scripts': [
            'webgui = main_entry:run_server',
        ],
    },
)
