"""Character page."""
from bson import ObjectId
from aiohttp_login.decorators import restricted_api
from aiohttp.web import json_response
from dnd.decorators import login_required
from dnd.common import format_errors

ABILITIES = [
    'strength',
    'dexterity',
    'constitution',
    'intelligence',
    'wisdom',
    'charisma',
    'perception']

def calculate_stats(character):
    """Calculate and set characters statistics."""
    ###########
    #  level  #
    ###########
    xp = 0 if 'xp' not in character else character['xp']
    level = 1
    while xp > 0:
        xp -= level * 100
        if xp >= 0:
            level += 1
    character['level'] = level
    ability_points_to_spend = int(level / 4)

    ###############
    #  abilities  #
    ###############
    spent_ability_points = 0
    for stat in ABILITIES:
        base_stat = '{}_base'.format(stat)
        base = character.get(base_stat, 0)
        character[base_stat] = base
        temp_stat = '{}_temp'.format(stat)
        temp = character.get(temp_stat, 0)
        character[temp_stat] = temp
        level_stat = '{}_level'.format(stat)
        level = character.get(level_stat, 0)
        spent_ability_points += level
        character[level_stat] = level
        # calculate bonus
        bonus_stat = '{}_bonus'.format(stat)
        bonus = 0
        character[bonus_stat] = bonus

        value = base + temp + level + bonus
        if value > 25:
            value = 25
        if value < 1:
            value = 1
        character[stat] = value

        modifier_stat = '{}_modifier'.format(stat)
        modifier = int((value - 10) // 3)
        if modifier < -3:
            modifier = -3
        if modifier > 5:
            modifier = 5
        character[modifier_stat] = modifier
    character['unspent_ability_points'] = ability_points_to_spend - spent_ability_points

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
            'data': character['unspent_ability_points']},
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
