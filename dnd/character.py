"""Character tools."""
import copy
from collections import OrderedDict
from pkg_resources import resource_stream, Requirement
from markupsafe import escape
from markdown import markdown
from yaml import load_all
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

RACES = {race['name']: race for race in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/races.yaml'),
    Loader=Loader) if race is not None}

SKILLS = {skill['name'].lower(): skill for skill in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/skills.yaml'),
    Loader=Loader) if skill is not None}

SKILL_GROUPS = {SKILLS[skill]['group'] for skill in SKILLS}

SPELLS = {spell['name'].lower(): spell for spell in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/spells.yaml'),
    Loader=Loader) if spell is not None}

PRAYERS = {prayer['name'].lower(): prayer for prayer in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/prayers.yaml'),
    Loader=Loader) if prayer is not None}

PRAYER_SPHERES = {PRAYERS[prayer]['sphere'] for prayer in PRAYERS}

WEAPONS = {weapon['name'].lower(): weapon for weapon in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/weapons.yaml'),
    Loader=Loader) if weapon is not None}

WEAPON_CATEGORIES = {WEAPONS[weapon]['weapon_category'] for weapon in WEAPONS}

WEAPON_SIZES = {size for weapon in WEAPONS for size in WEAPONS[weapon]['size']}

WEAPON_AGES = {
    age for weapon in WEAPONS \
    for size in WEAPONS[weapon]['size'] \
    for age in WEAPONS[weapon]['size'][size]['time_period']}

ARMOUR = {armour['name'].lower(): armour for armour in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/armour.yaml'),
    Loader=Loader) if armour is not None}

ARMOUR_AGES = {age for armour in ARMOUR for age in ARMOUR[armour]['time_period']}

POWERS = {power['name'].lower(): power for power in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/powers.yaml'),
    Loader=Loader) if power is not None}

ABILITIES = [
    'strength',
    'dexterity',
    'constitution',
    'intelligence',
    'wisdom',
    'charisma',
    'perception']

COINS = OrderedDict([
    ('oros', 1),
    ('dies', 24),
    ('semanis', 24 * 6),
    ('mensis', 24 * 6 * 5),
    ('annum', 24 * 6 * 5 * 12)])

CLASSES = {class_['name'].lower(): class_ for class_ in load_all(
    resource_stream(Requirement.parse('dnd'), 'dnd/config/classes.yaml'),
    Loader=Loader) if class_ is not None}

def convert_coins(coins):
    """
    Convert oros into higher coins, or a dictionary of higher coins into oros.
    """
    if isinstance(coins, int):
        result = {coin: 0 for coin in COINS}
        for coin in reversed(COINS):
            rest = coins % COINS[coin]
            if rest != coins:
                result[coin] = int((coins - rest) / COINS[coin])
                coins = rest
        return result
    elif isinstance(coins, dict):
        oros = 0
        for coin in coins:
            oros += COINS[coin] * coins[coin]
        return int(oros)

def calculate_stats(character):
    """Calculate and set characters statistics."""
    _character_level(character)
    _character_classes(character)
    _character_race(character)
    _character_abilities(character)
    _character_powers(character)
    _character_skills(character)
    _character_hit_points(character)
    _character_background(character)
    _character_spells(character)
    _character_prayers(character)
    _character_money(character)
    _character_inventory(character)
    _character_equipment(character)

def _character_level(character):
    xp = character.get('xp', 0)
    character['xp'] = xp
    level = 1
    while xp > 0:
        xp -= level * 100
        if xp >= 0:
            level += 1
    character['level'] = level

def _character_classes(character):
    for class_ in CLASSES:
        character[class_] = 0
    classes = character.get('classes', [])
    missing = character['level'] - len(classes)
    default_class = 'fighter' if len(classes) == 0 else classes[0]
    if missing > 0:
        classes.extend([default_class] * missing)
    elif missing < 0:
        classes = classes[:character['level']]
    character['classes'] = classes
    for i, class_ in enumerate(classes):
        if i < character['level']:
            character[class_] += 1

def _character_race(character):
    race_name = character.get('race_name', 'Truman')
    character['race_name'] = race_name
    character['race'] = RACES[race_name]

def _character_abilities(character):
    ability_points_to_spend = int(character['level'] / 4)
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

def _character_powers(character):
    power_names = character.get('power_names', [])
    character['powers'] = {}
    character['power_skill_slots'] = 0
    for power in power_names:
        character['power_skill_slots'] += 2
        if power in POWERS:
            character['powers'][power] = copy.deepcopy(POWERS[power])

def _character_skill_check(character, skill):
    if character['skills'][skill]['skill_check'] is None:
        character['skills'][skill]['skill_check_text'] = '-'
        character['skills'][skill]['skill_check_value'] = None
        return
    character['skills'][skill]['skill_check_text'] = ' + '.join([
        str(element) if not str(element).endswith(
            '_modifier') else "[{}]".format(
                element[0:-9]) for element in character['skills'][skill]['skill_check']])
    character['skills'][skill]['skill_check_value'] = sum([
        character[element]  if isinstance(
            element,
            str) else element for element in character['skills'][skill]['skill_check']])

def _character_skill_slots(character):
    class_skill_slots = 0
    for class_ in CLASSES:
        class_skill_slots += CLASSES[class_]['skill_slots'] * character[class_]
    skill_slots = 5 + class_skill_slots + character['intelligence_modifier']
    skill_slots -= character['power_skill_slots']
    if character['classes'][0] == "warlock":
        skill_slots += 1
    if 'skills' in character['race']['bonus']:
        skill_slots += character['race']['bonus']['skills']
    for skill in character['skills']:
        group = character['skills'][skill]['group']
        if group == 'all':
            skill_slots -= 1
        elif group in character and character[group] > 0:
            skill_slots -= 1
        elif group == 'magic' and (
                character['warlock'] > 0 or
                character['priest'] > 0 or
                character['wizard'] > 0):
            skill_slots -= 1
        else:
            skill_slots -= 2
    character['unspent_skill_slots'] = skill_slots

def _character_skills(character):
    skill_names = character.get('skill_names', [])
    character['skills'] = {}
    for skill in skill_names:
        if skill in SKILLS:
            character['skills'][skill] = copy.deepcopy(SKILLS[skill])
            _character_skill_check(character, skill)
    _character_skill_slots(character)

def _character_spells(character):
    spell_names = character.get('spell_names', [])
    character['spells'] = {}
    for spell in spell_names:
        spell = spell.lower()
        if spell in SPELLS:
            character['spells'][spell] = copy.deepcopy(SPELLS[spell])
    spell_slots = (
        tuple(),
        (2,),
        (2, 1),
        (3, 1),
        (3, 2),
        (3, 2, 1),
        (4, 2, 1),
        (4, 3, 1),
        (4, 3, 2),
        (4, 3, 2, 1),
        (5, 3, 2, 1),
        (5, 4, 2, 1),
        (5, 4, 3, 1),
        (5, 4, 3, 2),
        (5, 4, 3, 2, 1),
        (6, 4, 3, 2, 1),
        (6, 5, 3, 2, 1),
        (6, 5, 4, 2, 1),
        (6, 5, 4, 3, 1),
        (6, 5, 4, 3, 2),
        (6, 5, 4, 3, 2, 1))
    character['spell_slots'] = spell_slots[character['wizard']]
    character['invalid_prepared_spells'] = character.get(
        'invalid_prepared_spells', 0)
    leftover_spell_slots = list(character['spell_slots'])
    prepared_spells = character.get('prepared_spells', {})
    character['prepared_spells'] = prepared_spells
    for spell in prepared_spells:
        if SPELLS[spell]['circle'] > len(leftover_spell_slots):
            character['invalid_prepared_spells'] += prepared_spells[spell]['prepared']
            continue
        leftover_spell_slots[SPELLS[spell]['circle'] - 1] -= prepared_spells[spell]['prepared']
    debt_stack = []
    for i in range(len(leftover_spell_slots)):
        if leftover_spell_slots[i] < 0:
            debt_stack.append([i, leftover_spell_slots[i]])
        elif leftover_spell_slots[i] > 0 and len(debt_stack) > 0:
            overflow_room = leftover_spell_slots[i]
            for debt in debt_stack:
                if abs(debt[1]) >= overflow_room:
                    debt[1] += overflow_room
                    leftover_spell_slots[i] = 0
                    break
                else:
                    leftover_spell_slots[i] += debt[1]
                    debt[1] = 0
    for debt in debt_stack:
        leftover_spell_slots[debt[0]] = debt[1]
    character['leftover_spell_slots'] = leftover_spell_slots

def _character_prayers(character):
    prayer_names = set(character.get('prayer_names', []))
    spheres = set(character.get('prayer_spheres', {'all'}))
    prayer_slots = (
        tuple(),
        (1,),
        (2,),
        (2, 1),
        (2, 2),
        (3, 3),
        (3, 3, 1),
        (4, 3, 2),
        (4, 3, 2, 1),
        (4, 4, 2, 2),
        (5, 4, 3, 3),
        (5, 4, 3, 3, 1),
        (5, 4, 4, 3, 2),
        (5, 5, 4, 3, 2, 1),
        (5, 5, 4, 4, 2, 2),
        (5, 5, 5, 4, 3, 3),
        (5, 5, 5, 4, 3, 3, 1),
        (5, 5, 5, 4, 4, 3, 1),
        (5, 5, 5, 5, 4, 3, 1),
        (5, 5, 5, 5, 5, 4, 1),
        (5, 5, 5, 5, 5, 5, 2))
    character['prayer_slots'] = list(prayer_slots[character['priest']])
    if character['priest'] > 0:
        character['prayer_slots'][-1] += character['wisdom_modifier']
    for prayer in PRAYERS:
        if PRAYERS[prayer]['sphere'] in spheres and \
                PRAYERS[prayer]['circle'] <= len(character['prayer_slots']):
            prayer_names.add(prayer)
    character['prayers'] = {}
    for prayer in prayer_names:
        prayer = prayer.lower()
        if prayer in PRAYERS:
            character['prayers'][prayer] = copy.deepcopy(PRAYERS[prayer])
    character['invalid_prepared_prayers'] = character.get(
        'invalid_prepared_prayers', 0)
    leftover_prayer_slots = copy.copy(character['prayer_slots'])
    prepared_prayers = character.get('prepared_prayers', {})
    character['prepared_prayers'] = prepared_prayers
    for prayer in prepared_prayers:
        if PRAYERS[prayer]['circle'] > len(leftover_prayer_slots):
            character['invalid_prepared_prayers'] += prepared_prayers[prayer]['prepared']
            continue
        leftover_prayer_slots[PRAYERS[prayer]['circle'] - 1] -= prepared_prayers[prayer]['prepared']
    debt_stack = []
    for i in range(len(leftover_prayer_slots)):
        if leftover_prayer_slots[i] < 0:
            debt_stack.append([i, leftover_prayer_slots[i]])
        elif leftover_prayer_slots[i] > 0 and len(debt_stack) > 0:
            overflow_room = leftover_prayer_slots[i]
            for debt in debt_stack:
                if abs(debt[1]) >= overflow_room:
                    debt[1] += overflow_room
                    leftover_prayer_slots[i] = 0
                    break
                else:
                    leftover_prayer_slots[i] += debt[1]
                    debt[1] = 0
    for debt in debt_stack:
        leftover_prayer_slots[debt[0]] = debt[1]
    character['leftover_prayer_slots'] = leftover_prayer_slots

def _character_hit_points(character):
    per_level = character.get(
        'hitpoints_per_level',
        [0])
    per_level[0] = CLASSES[character['classes'][0]]['hitdie']
    missing = character['level'] - len(per_level)
    if missing > 0:
        per_level.extend([1] * missing)
    elif missing < 0:
        per_level = per_level[:character['level']]
    character['hitpoints_per_level'] = per_level
    max_hp = sum(per_level) + character['constitution_modifier'] * character['level']
    character['max_hp'] = max_hp
    temp_hp = character.get('temp_hp', 0)
    character['temp_hp'] = temp_hp
    damage = character.get('damage', 0)
    character['damage'] = damage
    character['hp'] = max_hp + temp_hp - damage

def _character_money(character):
    character['oros'] = character.get('oros', 0)
    character['coins'] = convert_coins(character['oros'])

def _character_inventory(character):
    character['inventory'] = character.get('inventory', {})
    for item in character['inventory']:
        character['inventory'][item]['description'] = markdown(escape(
            character['inventory'][item]['description_unsafe']))

def _character_equipment(character):
    character['weapons'] = character.get('weapons', [])
    character['armour'] = character.get('armour', [])

def _character_background(character):
    character['appearance_safe'] = markdown(escape(
        character.get('appearance_unsafe', '')))
    character['character_safe'] = markdown(escape(
        character.get('character_unsafe', '')))
    character['history_safe'] = markdown(escape(
        character.get('history_unsafe', '')))
