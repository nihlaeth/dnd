"""Character page."""
from bson import ObjectId
from aiohttp_login.decorators import restricted_api
from aiohttp.web import json_response
from dnd.decorators import login_required
from dnd.common import format_errors
from dnd.character import ABILITIES, RACES, SKILLS, CLASSES, calculate_stats

async def get_character(request):
    """Fetch character from database."""
    errors = []
    editing_privileges = False
    characters = request.app['db'].characters
    character = await characters.find_one(
        {'_id': ObjectId(request.match_info['id'])})
    if character is None:
        errors.append('character {} does not exist'.format(
            request.match_info['id']))
    else:
        if request['user'] == character['user']:
            editing_privileges = True
        calculate_stats(character)
    return (errors, editing_privileges, character)

@login_required(template_file='character.html')
async def character_handler(request):
    """Character page."""
    errors, editing_privileges, character = await get_character(request)
    return {
        'skills': SKILLS,
        'classes': CLASSES,
        'races': RACES,
        'abilities': ABILITIES,
        'editing_privileges': editing_privileges,
        'character': character,
        'errors': errors}

@restricted_api
async def data_handler(request):
    """Edit character attribute data."""
    errors, editing_privileges, character = await get_character(request)
    if not editing_privileges:
        errors.append("you don't have the required privileges to alter this character")
    attribute = request.match_info['attribute']
    attribute_functions = {
        'ability': (_ability_validator, _ability_response_factory),
        'xp': (_xp_validator, _xp_response_factory),
        'hp': (_hp_validator, _hp_response_factory),
        'race': (_race_validator, _race_response_factory),
        'class': (_class_validator, _class_response_factory),
    }
    if attribute not in attribute_functions:
        errors.append("unknown attribute")
    else:
        validator, response_factory = attribute_functions[attribute]
        await request.post()
        validated_data = validator(request, errors)
    if len(errors) == 0:
        characters = request.app['db'].characters
        result = await characters.update_one(
            {'_id': ObjectId(request.match_info['id'])},
            {'$set': validated_data})
        if not result.acknowledged:
            errors.append("database error")
    if len(errors) > 0:
        return json_response({'errors': format_errors(errors)})
    # no errors whatsoever, return data
    character = await characters.find_one(
        {'_id': ObjectId(request.match_info['id'])})
    calculate_stats(character)
    response = {'close': True}
    response_factory(response, character)
    return json_response(response)

def _ability_validator(request, errors):
    ability = request.match_info['ability']
    if ability not in ABILITIES:
        errors.append("invalid ability")
        return {}
    try:
        base = int(request.POST['base-{}'.format(ability)])
        level = int(request.POST['level-{}'.format(ability)])
        temp = int(request.POST['temp-{}'.format(ability)])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    return {
        ability + '_base': base,
        ability + '_level': level,
        ability + '_temp': temp}

def _ability_response_factory(response, character):
    for ability in ABILITIES:
        add_classes = []
        remove_classes = []
        if character[ability + '_temp'] < 0:
            add_classes.append('danger')
            remove_classes.append('success')
        elif character[ability + '_temp'] > 0:
            add_classes.append('success')
            remove_classes.append('danger')
        else:
            remove_classes.append('success')
            remove_classes.append('danger')
        response['#{}-value'.format(ability)] = {'data': character[ability]}
        response['#{}-modifier'.format(ability)] = {
            'data': character[ability + '_modifier']}
        response['#{}-row'.format(ability)] = {
            'addClass': add_classes,
            'removeClass': remove_classes}
    response['#ability-points'] = {
        'data': character['unspent_ability_points'],
        'addClass': ["label-danger"] if character[
            'unspent_ability_points'] < 0 else ["label-default"],
        'removeClass': ["label-danger"] if character[
            'unspent_ability_points'] >= 0 else ["label-default"]}

def _xp_validator(request, errors):
    try:
        xp = int(request.POST['xp'])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    return {'xp': xp}

def _xp_response_factory(response, character):
    response['#xp-value'] = {'data': character['xp']}
    response['#level-value'] = {'data': character['level']}

def _race_validator(request, errors):
    try:
        race = request.POST['race'].strip()
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    else:
        if race not in RACES:
            errors.append("unknown race: {}".format(race))
    return {'race_name': race}

def _race_response_factory(response, character):
    response['#inner-race-info'] = {
        'data': character['race']['description']}
    response['#race-value'] = {'data': character['race_name']}
    _ability_response_factory(response, character)

def _class_validator(request, errors):
    try:
        classes = {}
        for class_ in CLASSES:
            classes[class_] = int(request.POST[class_])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    return {class_: classes[class_] for class_ in CLASSES}

def _class_response_factory(response, character):
    class_list = "\n".join([
        "<li class=\"list-group-item\">{} <span class=\"label label-info\">{}</span></li>".format(
            class_.capitalize(),
            character[class_]) for class_ in CLASSES if character[class_] > 0])
    response['#class-value'] = {'data': class_list}
    response['#class-points'] = {
        'data': character['unspent_class_points'],
        'addClass': ["label-danger"] if character[
            'unspent_class_points'] < 0 else ["label-default"],
        'removeClass': ["label-danger"] if character[
            'unspent_class_points'] >= 0 else ["label-default"]}

def _hp_validator(request, errors):
    try:
        max_hp = int(request.POST['max-hp'])
        temp_hp = int(request.POST['temp-hp'])
        damage = int(request.POST['damage'])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    return {
        'max_hp': max_hp,
        'temp_hp': temp_hp,
        'damage': damage}

def _hp_response_factory(response, character):
    add_classes = []
    remove_classes = []
    if character['damage'] > 0:
        add_classes.append('danger')
        remove_classes.append('success')
        remove_classes.append('warning')
    elif character['temp_hp'] < 0:
        add_classes.append('warning')
        remove_classes.append('success')
        remove_classes.append('danger')
    elif character['temp_hp'] > 0:
        add_classes.append('success')
        remove_classes.append('danger')
        remove_classes.append('warning')
    else:
        remove_classes.append('success')
        remove_classes.append('danger')
        remove_classes.append('warning')
    rest_in_peace = "" if character['hp'] > -10 else "<span class=\"badge\">R.I.P</span>"
    response['#hp-value'] = {'data': character['hp']}
    response['#alive'] = {'data': rest_in_peace}
    response['#hp-row'] = {
        'addClass': add_classes,
        'removeClass': remove_classes}
