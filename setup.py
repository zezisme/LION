import os
import setuptools

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


packages = setuptools.find_namespace_packages()

setuptools.setup(
    name="LION",
    version="0.2",
    author="Ander Biguri",
    author_email="ander.biguri@gmail.com",
    description=("Tomographic tools for AI-driven reconstruction"),
    license="BSD",
    keywords="CT, AI",
    url="-",
    packages=packages,
    long_description=read("README.md"),
)

# os.system("pip install ./LION/models/MS-D/")

wd = os.getcwd()
os.chdir("./LION/metrics/radiomics/")
os.system("pip install .")
os.chdir(wd)
