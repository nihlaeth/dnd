"""Handy decorators."""
from functools import wraps
import aiohttp_login
from aiohttp_jinja2 import template

from dnd.character import calculate_stats

def login_required(template_file):
    """
    Require user to be logged in and pass necessary data for navigation bar.
    """
    def decorator(handler):
        @aiohttp_login.login_required
        @template(template_file)
        @wraps(handler)
        async def inner_decorator(request):
            result = await handler(request)
            characters = request.app['db'].characters
            result['characters'] = await characters.find(
                {'user': request['user']}).to_list(length=100)
            for character in result['characters']:
                calculate_stats(character)
            campaigns = request.app['db'].campaigns
            result['campaigns'] = await campaigns.find(
                {'user': request['user']}).to_list(length=100)
            return result
        return inner_decorator
    return decorator
