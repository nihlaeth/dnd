"""Character tools."""
from pkg_resources import resource_stream, Requirement
from yaml import load_all
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

RACES = {race['name']: race for race in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/races.yaml'),
    Loader=Loader) if race is not None}


SKILLS = {skill['name']: skill for skill in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/skills.yaml'),
    Loader=Loader) if skill is not None}

ABILITIES = [
    'strength',
    'dexterity',
    'constitution',
    'intelligence',
    'wisdom',
    'charisma',
    'perception']

CLASSES = [
    'fighter',
    'specialist',
    'wizard',
    'priest',
    'warlock']

def calculate_stats(character):
    """Calculate and set characters statistics."""
    ###########
    #  level  #
    ###########
    xp = character.get('xp', 0)
    character['xp'] = xp
    level = 1
    while xp > 0:
        xp -= level * 100
        if xp >= 0:
            level += 1
    character['level'] = level
    ability_points_to_spend = int(level / 4)

    #############
    #  classes  #
    #############
    unspent_class_points = level
    for class_ in CLASSES:
        value = character.get(class_, 0)
        unspent_class_points -= value
        character[class_] = value
    character['unspent_class_points'] = unspent_class_points

    ###########
    #  races  #
    ###########
    race_name = character.get('race_name', 'Truman')
    character['race_name'] = race_name
    character['race'] = RACES[race_name]

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
        spent_ability_points += abs(level)
        character[level_stat] = level
        # calculate bonus
        bonus_stat = '{}_bonus'.format(stat)
        bonus = character['race']['bonus'].get(stat, 0)
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

    ############
    #  skills  #
    ############
    skills = character.get('skills', {})
    skill_points = 5 + character['level'] + character['intelligence_modifier']
    if 'skills' in character['race']['bonus']:
        skill_points += character['race']['bonus']['skills']
    for skill in skills:
        group = skills[skill]['group']
        if group == 'all':
            skill_points -= 1
        elif group in character['classes']:
            skill_points -= 1
        elif group == 'magic' and (
                'sorcerer' in character['classes'] or
                'priest' in character['classes'] or
                'wizard' in character['classes']):
            skill_points -= 1
        else:
            skill_points -= 2
    character['unspent_skill_points'] = skill_points

    ###############
    #  hitpoints  #
    ###############
    max_hp = character.get('max_hp', 1)
    if max_hp < 1:
        max_hp = 1
    character['max_hp'] = max_hp
    temp_hp = character.get('temp_hp', 0)
    character['temp_hp'] = temp_hp
    damage = character.get('damage', 0)
    character['damage'] = damage
    character['hp'] = max_hp + temp_hp - damage
