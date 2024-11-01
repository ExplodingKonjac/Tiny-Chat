from setuptools import setup, find_packages

setup(
	name="Tiny Chat",
	version="0.1.0",
	author="ExplodingKonjac",
	description="A simple chat program in LAN",
	long_description=open("README.md").read(),
	long_description_content_type="text/markdown",
	url="https://github.com/ExplodingKonjac/Tiny-Chat",
	packages=find_packages(),
	install_requires=[
		"wcwidth>=0.2.5",
		"curses"
	],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GPLv3 License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.12',
	entry_points={
		"console_scripts": [
			"tinychat=tinychat.main:main",
		]
	},
)
