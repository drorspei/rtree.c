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

from distutils.command.build_ext import build_ext as build_ext_orig
class CTypesExtension(Extension): pass
class build_ext(build_ext_orig):
    def build_extension(self, ext):
        #import pdb;pdb.set_trace()
        print("build_extension!!!")
        self._ctypes = isinstance(ext, CTypesExtension)
        return super().build_extension(ext)

    def get_export_symbols(self, ext):
        print("get_export_symbols")
        if self._ctypes:
            return ext.export_symbols
        return super().get_export_symbols(ext)

    def get_ext_filename(self, ext_name):
        print("get_ext_filename")
        if self._ctypes:
            return ext_name + '.so'
        return super().get_ext_filename(ext_name)

module = CTypesExtension('rtreecpy.librtreec',
                   ['rtreecpy/rtree.cpp', 'rtreecpy/batch_search.cpp'],
                   #include_dirs = [''],
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
    #cmdclass={'install': CustomInstall},
    py_modules=["rtreecpy"],
    cmdclass={'build_ext': build_ext},
    ext_modules=[module],
)


