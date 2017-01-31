"""Installation script for dnd."""
from setuptools import setup, find_packages

setup(
    name='dnd',
    version='1.0',
    description='online character sheets for Dungeons & Dragons v2.thomaas',
    author='nihlaeth',
    author_email='info@nihlaeth.nl',
    python_requires='>=3.6',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'markupsafe',
        'aiohttp_session[secure]',
        'Jinja2',
        'aiohttp_jinja2',
        'motor',
        'cchardet',
        'aiodns',
        'aiohttp-login'],
    entry_points={
        'console_scripts': ['dnd = dnd:start']},
    package_data={'dnd': ['static/*', 'templates/*']},
    )
