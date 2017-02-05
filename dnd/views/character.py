"""Character page."""
from bson import ObjectId
from aiohttp_login.decorators import restricted_api
from aiohttp.web import json_response
from dnd.decorators import login_required
from dnd.common import format_errors
from dnd.character import ABILITIES, RACES, SKILLS, CLASSES, calculate_stats

async def get_character(request):
    """Fetch character from database."""
    successes = []
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
    return (successes, errors, editing_privileges, character)

@login_required(template_file='character.html')
async def character_handler(request):
    """Character page."""
    successes, errors, editing_privileges, character = await get_character(request)
    return {
        'skills': SKILLS,
        'classes': CLASSES,
        'races': RACES,
        'abilities': ABILITIES,
        'editing_privileges': editing_privileges,
        'character': character,
        'successes': successes,
        'errors': errors}

@restricted_api
async def ability_data_handler(request):
    """Edit character attribute data."""
    _, errors, editing_privileges, character = await get_character(request)
    if not editing_privileges:
        errors.append("you don't have the required privileges to alter this character")
    ability = request.match_info['ability']
    if ability not in ABILITIES:
        errors.append("invalid ability")
    await request.post()
    try:
        base = int(request.POST['base-{}'.format(ability)])
        level = int(request.POST['level-{}'.format(ability)])
        temp = int(request.POST['temp-{}'.format(ability)])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    if len(errors) == 0:
        characters = request.app['db'].characters
        result = await characters.update_one(
            {'_id': ObjectId(request.match_info['id'])},
            {'$set': {
                ability + '_base': base,
                ability + '_level': level,
                ability + '_temp': temp}})
        if not result.acknowledged:
            errors.append("database error")
    if len(errors) > 0:
        return json_response({'errors': format_errors(errors)})
    # no errors whatsoever, return data
    character = await characters.find_one(
        {'_id': ObjectId(request.match_info['id'])})
    calculate_stats(character)
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
    return json_response({
        'close': True,
        '#{}-value'.format(ability): {'data': character[ability]},
        '#{}-modifier'.format(ability): {
            'data': character[ability + '_modifier']},
        '#ability-points': {
            'data': character['unspent_ability_points'],
            'addClass': ["label-danger"] if character[
                'unspent_ability_points'] < 0 else ["label-default"],
            'removeClass': ["label-danger"] if character[
                'unspent_ability_points'] >= 0 else ["label-default"]},
        '#{}-row'.format(ability): {
            'addClass': add_classes,
            'removeClass': remove_classes}})

@restricted_api
async def xp_data_handler(request):
    """Edit character xp data."""
    _, errors, editing_privileges, character = await get_character(request)
    if not editing_privileges:
        errors.append("you don't have the required privileges to alter this character")
    await request.post()
    try:
        xp = int(request.POST['xp'])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    if len(errors) == 0:
        characters = request.app['db'].characters
        result = await characters.update_one(
            {'_id': ObjectId(request.match_info['id'])},
            {'$set': {'xp': xp}})
        if not result.acknowledged:
            errors.append("database error")
    if len(errors) > 0:
        return json_response({'errors': format_errors(errors)})
    # no errors whatsoever, return data
    character = await characters.find_one(
        {'_id': ObjectId(request.match_info['id'])})
    calculate_stats(character)
    return json_response({
        'close': True,
        '#xp-value': {'data': character['xp']},
        '#level-value': {'data': character['level']}})

@restricted_api
async def race_data_handler(request):
    """Edit character race data."""
    _, errors, editing_privileges, character = await get_character(request)
    if not editing_privileges:
        errors.append("you don't have the required privileges to alter this character")
    await request.post()
    try:
        race = request.POST['race'].strip()
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    else:
        if race not in RACES:
            errors.append("unknown race: {}".format(race))
    if len(errors) == 0:
        characters = request.app['db'].characters
        result = await characters.update_one(
            {'_id': ObjectId(request.match_info['id'])},
            {'$set': {'race_name': race}})
        if not result.acknowledged:
            errors.append("database error")
    if len(errors) > 0:
        return json_response({'errors': format_errors(errors)})
    # no errors whatsoever, return data
    character = await characters.find_one(
        {'_id': ObjectId(request.match_info['id'])})
    calculate_stats(character)
    return json_response({
        'close': True,
        '#inner-race-info': {'data': character['race']['description']},
        '#race-value': {'data': character['race_name']}})

@restricted_api
async def class_data_handler(request):
    """Edit character class data."""
    _, errors, editing_privileges, character = await get_character(request)
    if not editing_privileges:
        errors.append("you don't have the required privileges to alter this character")
    await request.post()
    try:
        classes = {}
        for class_ in CLASSES:
            classes[class_] = int(request.POST[class_])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    if len(errors) == 0:
        characters = request.app['db'].characters
        result = await characters.update_one(
            {'_id': ObjectId(request.match_info['id'])},
            {'$set': {class_: classes[class_] for class_ in CLASSES}})
        if not result.acknowledged:
            errors.append("database error")
    if len(errors) > 0:
        return json_response({'errors': format_errors(errors)})
    # no errors whatsoever, return data
    character = await characters.find_one(
        {'_id': ObjectId(request.match_info['id'])})
    calculate_stats(character)
    class_list = "\n".join([
        "<li class=\"list-group-item\">{} <span class=\"label label-info\">{}</span></li>".format(
            class_.capitalize(),
            character[class_]) for class_ in CLASSES if character[class_] > 0])
    return json_response({
        'close': True,
        '#class-value': {'data': class_list},
        '#class-points': {
            'data': character['unspent_class_points'],
            'addClass': ["label-danger"] if character[
                'unspent_class_points'] < 0 else ["label-default"],
            'removeClass': ["label-danger"] if character[
                'unspent_class_points'] >= 0 else ["label-default"]}})

@restricted_api
async def hp_data_handler(request):
    """Edit character hp data."""
    _, errors, editing_privileges, character = await get_character(request)
    if not editing_privileges:
        errors.append("you don't have the required privileges to alter this character")
    await request.post()
    try:
        max_hp = int(request.POST['max-hp'])
        temp_hp = int(request.POST['temp-hp'])
        damage = int(request.POST['damage'])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    if len(errors) == 0:
        characters = request.app['db'].characters
        result = await characters.update_one(
            {'_id': ObjectId(request.match_info['id'])},
            {'$set': {
                'max_hp': max_hp,
                'temp_hp': temp_hp,
                'damage': damage}})
        if not result.acknowledged:
            errors.append("database error")
    if len(errors) > 0:
        return json_response({'errors': format_errors(errors)})
    # no errors whatsoever, return data
    character = await characters.find_one(
        {'_id': ObjectId(request.match_info['id'])})
    calculate_stats(character)
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
    return json_response({
        'close': True,
        '#hp-value': {'data': character['hp']},
        '#alive': {
            'data': rest_in_peace},
        '#hp-row': {
            'addClass': add_classes,
            'removeClass': remove_classes}})
