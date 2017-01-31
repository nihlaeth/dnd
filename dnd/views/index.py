"""Index page."""
from datetime  import datetime
from markupsafe import escape
from aiohttp_login.decorators import restricted_api
from aiohttp.web import json_response
from dnd.decorators import login_required
from dnd.common import format_errors

@login_required(template_file='index.html')
async def index_handler(request):
    """Index page."""
    successes = []
    errors = []
    return {
        'successes': successes,
        'errors': errors}

@restricted_api
async def new_character_data_handler(request):
    """Create new character."""
    errors = []
    await request.post()
    try:
        name = escape(request.POST['name'].strip())
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    if name is not None and (len(name) < 1 or len(name) > 50):
        errors.append("length should be between one and fifty characters")
    if len(errors) == 0:
        characters = request.app['db'].characters
        if await characters.find_one(
                {'user': request['user'], 'name': name}) is not None:
            errors.append("you already have a character with this name")
        else:
            result = await characters.insert_one({
                'user': request['user'],
                'name': name,
                'xp': 0,
                'hp': 0,
                'created_at': datetime.now()})
            if result.acknowledged:
                character = await characters.find_one({
                    '_id': result.inserted_id})
                table_row = """
<tr>
    <td>
        <a href="/{}/{}/" class="btn btn-default" role="button">{}</a>
    </td>
    <td>{}</td>
    <td>{}</td>
</tr>""".format(character['_id'],
                character['name'],
                character['name'],
                character['created_at'].date(),
                "")
                return json_response({
                    'close': True,
                    '#character-table': {'appendTable': table_row}})
            else:
                errors.append("computer says no")
    if len(errors) > 0:
        return json_response({'errors': format_errors(errors)})
