"""Index page."""
from datetime  import datetime
from markupsafe import escape
from aiohttp_login.decorators import restricted_api, login_required
from aiohttp.web import json_response, Response
from dnd.common import format_errors
from dnd.character import calculate_stats
from dnd.themes.default.index import index_page

@login_required
async def index_handler(request):
    """Index page."""
    characters_collection = request.app['db'].characters
    invalid_characters = await characters_collection.find(
        {'user._id': request['user']['_id']}).to_list(length=100)
    for character in invalid_characters:
        await characters_collection.update_one(
            {'_id': character['_id']},
            {
                '$set': {'user_id': request['user']['_id']},
                '$unset': {'user': True}})
    characters = await characters_collection.find(
        {'user_id': request['user']['_id']}).to_list(length=100)
    for character in characters:
        calculate_stats(character)
    return Response(text=index_page(characters).render(), content_type='text/html')

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
    if not errors:
        characters = request.app['db'].characters
        if await characters.find_one(
                {'user_id': request['user']['_id'], 'name': name}) is not None:
            errors.append("you already have a character with this name")
        else:
            result = await characters.insert_one({
                'user_id': request['user']['_id'],
                'name': name,
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
</tr>""".format(character['_id'],
                character['name'],
                character['name'],
                character['created_at'].date())
                return json_response({
                    'close': True,
                    '#character-table': {'appendTable': table_row}})
            else:
                errors.append("computer says no")
    if errors:
        return json_response({'errors': format_errors(errors)})
