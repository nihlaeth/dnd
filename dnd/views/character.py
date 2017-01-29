"""Character page."""
from datetime import datetime
from wtforms import Form, StringField, validators
from dnd.decorators import login_required
from bson import ObjectId

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
    stats = [
        'strength',
        'dexterity',
        'constitution',
        'intelligence',
        'wisdom',
        'charisma',
        'perception']
    spent_ability_points = 0
    for stat in stats:
        base_stat = '{}_base'.format(stat)
        base = 0 if base_stat not in character else character[base_stat]
        character[base_stat] = base
        temp_stat = '{}_temp'.format(stat)
        temp = 0 if temp_stat not in character else character[temp_stat]
        character[temp_stat] = temp
        level_stat = '{}_level'.format(stat)
        level = 0 if level_stat not in character else character[level_stat]
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
        modifier = int((value - 10) / 3)
        if modifier < -3:
            modifier = -3
        if modifier > 5:
            modifier = 5
        character[modifier_stat] = modifier
    character['unspent_ability_points'] = ability_points_to_spend - spent_ability_points


@login_required(template_file='character.html')
async def character_handler(request):
    """Character page."""
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
    return {
        'editing_privileges': editing_privileges,
        'character': character,
        'successes': successes,
        'errors': errors}
