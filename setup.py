from pybkotec import version

from setuptools import setup, find_packages

with open("README.md") as fp:
	readme = fp.read()

with open("requirements.txt") as fp:
	requirements = fp.read().splitlines()

setup(
	name="pybkotec",
	version=version,
	packages=find_packages(),
	
	install_requires=requirements,
	
	author="Eero Molkoselkä",
	author_email="eero.molkoselka@gmail.com",
	description="Unofficial software for Labkotec sensors",
	long_description=readme,
	url="https://github.com/molkoback/pybkotec",
	license="MIT",
	
	entry_points={
		"console_scripts": [
			"lid-3300ip = pybkotec.lid3300ip:main"
		]
	},
	
	classifiers=[
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3",
		"Topic :: Scientific/Engineering :: Atmospheric Science",
		"Topic :: Software Development :: Embedded Systems"
	]
)
