"""Index page."""
from aiohttp_jinja2 import template
from aiohttp_login import login_required

@login_required
@template('index.html')
async def index_handler(request):
    characters = request.app['db'].characters
    user_characters = await characters.find(
        {'user': request['user']}).to_list(length=100)
    campaigns = request.app['db'].campaigns
    user_campaigns = await campaigns.find(
        {'user': request['user']}).to_list(length=100)

    return {'characters': user_characters, 'campaigns': user_campaigns}
