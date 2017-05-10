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
        'user_config',
        'aiohttp',
        'aiosmtplib>=1.0.1',
        'markupsafe',
        'markdown',
        'aiohttp_session[secure]',
        'Jinja2',
        'aiohttp_jinja2',
        'motor',
        'cchardet',
        'aiodns',
        'aiohttp-login',
        'pyyaml',
        'uvloop',
        'pyhtml>=1.1.2',
        'roman'],
    entry_points={
        'console_scripts': ['dnd = dnd:start']},
    package_data={'dnd': ['static/*', 'templates/*', 'config/*']},
    )
