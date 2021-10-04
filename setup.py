from setuptools import setup, Extension, find_packages
from setuptools.command.install import install
import subprocess
import os

class CustomInstall(install):
    def run(self):
        command = "git clone https://github.com/drorspei/rtree.c"
        process = subprocess.Popen(command, shell=True, cwd=".")
        process.wait()
        install.run(self)

module = Extension('rtreecpy',
                   sources = ['rtree.cpp', 'batch_search.cpp'],
                   include_dirs = ['.'],
                   extra_compile_args=['-fPIC', '-O3', '-shared', '-fpermissive'])


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="rtreecpy",
    version="1.0.0",
    author="dror",
    author_email="dror.mastershin@gmail.com",
    description="rtree c python bindings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/drorspei/rtree.c",
    packages=find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    cmdclass={'install': CustomInstall},
    ext_modules=[module],
)


