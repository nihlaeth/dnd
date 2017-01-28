"""Index page."""
from datetime import datetime
from wtforms import Form, StringField, validators
from dnd.decorators import login_required

@login_required(template_file='index.html')
async def index_handler(request):
    """Index page."""
    successes = []
    errors = []
    await request.post()
    character_form = CreateCharacterForm(request.POST)
    if request.method == 'POST' and character_form.validate():
        name = character_form.character_name.data
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
                character_form.character_name.data = None
                successes.append("creating character")
            else:
                errors.append("computer says no")
    return {
        'character_form': character_form,
        'successes': successes,
        'errors': errors}

class CreateCharacterForm(Form):

    """Form to create a new character."""

    character_name = StringField(
        'name', [validators.length(min=1, max=30)])
