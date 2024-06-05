from setuptools import setup, find_packages

setup(
    name='WebGUI',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'PyYAML~=6.0.0',
        'tornado~=6.3.3',
        'setuptools~=49.2.1',
        'python-dateutil>=2.8.2',
        'testresources',
        'viswaternet~=1.1.0',
        'matplotlib~=3.5.0',
        'pillow>=8.3.2'
    ],
    entry_points={
        'console_scripts': [
            'webgui = main_entry:run_server',
        ],
    },
)
