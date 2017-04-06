"""Character page."""
import time
import re
from inspect import iscoroutinefunction
from bson import ObjectId
from aiohttp_login.decorators import restricted_api
from aiohttp.web import json_response
from markupsafe import escape
from aiohttp_jinja2 import get_env
from dnd.decorators import login_required
from dnd.common import format_errors
from dnd.character import (
    ABILITIES,
    RACES,
    SKILLS,
    SPELLS,
    PRAYERS,
    PRAYER_SPHERES,
    POWERS,
    CLASSES,
    COINS,
    WEAPONS,
    WEAPON_CATEGORIES,
    WEAPON_SIZES,
    WEAPON_AGES,
    ARMOUR,
    ARMOUR_AGES,
    convert_coins,
    calculate_stats)

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
        if request['user']['_id'] == character['user_id']:
            editing_privileges = True
        calculate_stats(character)
    return (errors, editing_privileges, character)

@login_required(template_file='character.html')
async def character_handler(request):
    """Character page."""
    errors, editing_privileges, character = await get_character(request)
    return {
        'spells': SPELLS,
        'prayers': PRAYERS,
        'prayer_spheres': PRAYER_SPHERES,
        'powers': POWERS,
        'skills': SKILLS,
        'classes': CLASSES,
        'races': RACES,
        'abilities': ABILITIES,
        'coins': COINS,
        'weapons': WEAPONS,
        'weapon_categories': WEAPON_CATEGORIES,
        'weapon_sizes': WEAPON_SIZES,
        'weapon_ages': WEAPON_AGES,
        'armour': ARMOUR,
        'armour_ages': ARMOUR_AGES,
        'editing_privileges': editing_privileges,
        'character': character,
        'errors': errors}

@restricted_api
async def data_handler(request):
    """Edit character attribute data."""
    errors, editing_privileges, character = await get_character(request)
    if not editing_privileges:
        errors.append("you don't have the required privileges to alter this character")
    user = await request.app['db'].users.find_one(
        {'_id': ObjectId(request['user']['_id'])})
    if 'last_action' in user and abs(user['last_action'] - time.perf_counter()) < 0.125:
        return json_response({})
    result = await request.app['db'].users.update_one(
        {'_id': ObjectId(user['_id'])},
        {'$set': {'last_action': time.perf_counter()}})
    if not result.acknowledged:
        errors.append("database error")

    attribute = request.match_info['attribute']
    attribute_functions = {
        'ability': (_ability_validator, _ability_response_factory),
        'xp': (_xp_validator, _xp_response_factory),
        'hp': (_hp_validator, _hp_response_factory),
        'race': (_race_validator, _race_response_factory),
        'class': (_class_validator, _class_response_factory),
        'skill': (_skill_validator, _skill_response_factory),
        'spell': (_spell_validator, _spell_response_factory),
        'prepare_spell': (_prepare_spell_validator, _prepare_spell_response_factory),
        'prayer': (_prayer_validator, _prayer_response_factory),
        'prepare_prayer': (_prepare_prayer_validator, _prepare_prayer_response_factory),
        'power': (_power_validator, _power_response_factory),
        'name': (_name_validator, _name_response_factory),
        'background': (_background_validator, _background_response_factory),
        'inventory': (_inventory_validator, _inventory_response_factory),
        'coin': (_coin_validator, _coin_response_factory),
        'rest': (_rest_validator, _rest_response_factory),
    }
    if attribute not in attribute_functions:
        errors.append("unknown attribute")
    else:
        validator, response_factory = attribute_functions[attribute]
        await request.post()
        if iscoroutinefunction(validator):
            validated_data = await validator(request, errors)
        else:
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
    if 'type' in request.POST and request.POST['type'] == 'action':
        response = {'close': False}
    else:
        response = {'close': True}
    if iscoroutinefunction(response_factory):
        await response_factory(response, character, request.app)
    else:
        response_factory(response, character, request.app)
    return json_response(response)

def _ability_validator(request, errors):
    ability = request.match_info['extra']
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

def _ability_response_factory(response, character, app):
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
    _skill_response_factory(response, character, app)
    _prayer_response_factory(response, character, app)
    _hp_response_factory(response, character, app)

def _xp_validator(request, errors):
    try:
        xp = int(request.POST['xp'])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    return {'xp': xp}

def _xp_response_factory(response, character, app):
    response['#xp-value'] = {'data': character['xp']}
    response['#level-value'] = {'data': character['level']}
    _skill_response_factory(response, character, app)
    _class_response_factory(response, character, app)
    _hp_response_factory(response, character, app)

def _race_validator(request, errors):
    try:
        race = request.POST['race'].strip()
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    else:
        if race not in RACES:
            errors.append("unknown race: {}".format(race))
    return {'race_name': race}

def _race_response_factory(response, character, app):
    response['#inner-race-info'] = {
        'data': character['race']['description']}
    response['#race-value'] = {'data': character['race_name']}
    _ability_response_factory(response, character, app)
    _skill_response_factory(response, character, app)

def _class_validator(request, errors):
    classes = []
    i = 1
    try:
        while True:
            class_ = request.POST[str(i)]
            if class_ not in CLASSES:
                errors.append("invalid class: {}".format(class_))
            else:
                classes.append(class_)
            i += 1
    except KeyError:
        pass
    return {'classes': classes}

def _class_response_factory(response, character, app):
    class_list = "\n".join(["""
<li class="list-group-item">
  {}
  <span class="label label-default">{}</span>
  <button type="button" class="btn btn-info btn-xs" data-toggle="collapse" data-parent="#class-group" data-target="#{}-info-dynamic">?</button>
</li>""".format(
            class_.capitalize(),
            character[class_],
            class_,
            class_) for class_ in CLASSES if character[class_] > 0])
    response['#class-value'] = {'data': class_list}
    response['#prayer-section'] = {
        'collapse': "show" if character['priest'] > 0 else "hide"}
    response['#spells-section'] = {
        'collapse': "show" if character['wizard'] > 0 else "hide"}
    response['#powers-section'] = {
        'collapse': "show" if character['warlock'] > 0 else "hide"}
    response['#class-form-content'] = {
        'data': get_env(app).get_template(
            'character_class_form.html').render(
                character=character, classes=CLASSES),
        'activateTooltip': True}
    _skill_response_factory(response, character, app)
    _spell_response_factory(response, character, app)
    _prayer_response_factory(response, character, app)
    _hp_response_factory(response, character, app)

def _hp_validator(request, errors):
    per_level = []
    i = 1
    try:
        while True:
            try:
                hit_level = int(request.POST[str(i)])
            except ValueError:
                errors.append("invalid value: {} (expected integer)".format(hit_level))
            else:
                per_level.append(hit_level)
            i += 1
    except KeyError:
        pass
    try:
        temp_hp = int(request.POST['temp-hp'])
        damage = int(request.POST['damage'])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    return {
        'hitpoints_per_level': per_level,
        'temp_hp': temp_hp,
        'damage': damage}

def _hp_response_factory(response, character, app):
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
    response['#hp-form-content'] = {
        'data': get_env(app).get_template(
            'character_hp_form.html').render(
                character=character, classes=CLASSES),
        'activateTooltip': True}
    response['#hp-value'] = {'data': character['hp']}
    response['#alive'] = {'data': rest_in_peace}
    response['#hp-row'] = {
        'addClass': add_classes,
        'removeClass': remove_classes}

def _skill_validator(request, _):
    skills = []
    for skill in SKILLS:
        if skill in request.POST:
            skills.append(skill)
    return {'skill_names': skills}

def _skill_response_factory(response, character, app):
    response['#skill-accordion'] = {
        'data': get_env(app).get_template(
            'character_skills_display.html').render(character=character),
        'activateTooltip': True}
    response['#skill-slots'] = {
        'data': character['unspent_skill_slots'],
        'addClass': ["label-danger"] if character[
            'unspent_skill_slots'] < 0 else ["label-default"],
        'removeClass': ["label-danger"] if character[
            'unspent_skill_slots'] >= 0 else ["label-default"]}

def _spell_validator(request, _):
    spells = []
    for spell in SPELLS:
        if spell in request.POST:
            spells.append(spell)
    return {'spell_names': spells}

def _spell_response_factory(response, character, app):
    response['#spell-accordion'] = {
        'data': get_env(app).get_template(
            'character_spells_display.html').render(
                spells=SPELLS, character=character),
        'activateTooltip': True}
    response['#spell-slots'] = {
        'data': get_env(app).get_template(
            'character_spell_slots.html').render(character=character)}

async def _prepare_spell_validator(request, errors):
    action = request.match_info['extra']
    if action not in ['prepare', 'cast', 'forget']:
        errors.append("invalid action")
        return {}
    try:
        name = request.POST['name']
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    more_errors, _, character = await get_character(request)
    errors.extend(more_errors)
    if len(errors) != 0:
        return {}
    if action == 'prepare':
        if name not in character['spells']:
            errors.append('{} is unknown to character'.format(name))
        else:
            if name not in character['prepared_spells']:
                character['prepared_spells'][name] = {'prepared': 0, 'cast': 0}
            character['prepared_spells'][name]['prepared'] += 1
    elif action == 'cast':
        if name not in character['prepared_spells']:
            errors.append('{} is not a prepared spell'.format(name))
        elif character['prepared_spells'][name]['cast'] + 1 > \
                character['prepared_spells'][name]['prepared']:
            errors.append('not enough spells prepared')
        else:
            character['prepared_spells'][name]['cast'] += 1
    elif action == 'forget':
        if name not in character['prepared_spells']:
            errors.append('{} is not a prepared spell'.format(name))
        else:
            character['prepared_spells'][name]['prepared'] -= 1
            if character['prepared_spells'][name]['cast'] > \
                    character['prepared_spells'][name]['prepared']:
                character['prepared_spells'][name]['cast'] = \
                        character['prepared_spells'][name]['prepared']
            if character['prepared_spells'][name]['prepared'] == 0:
                del character['prepared_spells'][name]
    return {'prepared_spells': character['prepared_spells']}

def _prepare_spell_response_factory(response, character, app):
    response['close'] = False
    response['#prepared-spells'] = {
        'data': get_env(app).get_template(
            'character_prepared_spells.html').render(
                spells=SPELLS, character=character)}
    response['#spell-slots'] = {
        'data': get_env(app).get_template(
            'character_spell_slots.html').render(character=character)}

def _prayer_validator(request, errors):
    spheres = {'all'}
    for number in range(1, 4):
        try:
            sphere = request.POST[str(number)]
        except KeyError as error:
            errors.append("missing value: {}".format(error))
        if sphere not in PRAYER_SPHERES:
            errors.append("{} is not a valid prayer sphere".format(sphere))
        else:
            spheres.add(sphere)
    return {'prayer_spheres': list(spheres)}

def _prayer_response_factory(response, character, app):
    response['#prayer-accordion'] = {
        'data': get_env(app).get_template(
            'character_prayers_display.html').render(
                prayers=PRAYERS, character=character),
        'activateTooltip': True}
    response['#prayer-slots'] = {
        'data': get_env(app).get_template(
            'character_prayer_slots.html').render(character=character)}

async def _prepare_prayer_validator(request, errors):
    action = request.match_info['extra']
    if action not in ['prepare', 'cast', 'forget']:
        errors.append("invalid action")
        return {}
    try:
        name = request.POST['name']
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    more_errors, _, character = await get_character(request)
    errors.extend(more_errors)
    if len(errors) != 0:
        return {}
    if action == 'prepare':
        if name not in character['prayers']:
            errors.append('{} is unknown to character'.format(name))
        else:
            if name not in character['prepared_prayers']:
                character['prepared_prayers'][name] = {'prepared': 0, 'cast': 0}
            character['prepared_prayers'][name]['prepared'] += 1
    elif action == 'cast':
        if name not in character['prepared_prayers']:
            errors.append('{} is not a prepared prayer'.format(name))
        elif character['prepared_prayers'][name]['cast'] + 1 > \
                character['prepared_prayers'][name]['prepared']:
            errors.append('not enough prayers prepared')
        else:
            character['prepared_prayers'][name]['cast'] += 1
    elif action == 'forget':
        if name not in character['prepared_prayers']:
            errors.append('{} is not a prepared prayer'.format(name))
        else:
            character['prepared_prayers'][name]['prepared'] -= 1
            if character['prepared_prayers'][name]['cast'] > \
                    character['prepared_prayers'][name]['prepared']:
                character['prepared_prayers'][name]['cast'] = \
                        character['prepared_prayers'][name]['prepared']
            if character['prepared_prayers'][name]['prepared'] == 0:
                del character['prepared_prayers'][name]
    return {'prepared_prayers': character['prepared_prayers']}

def _prepare_prayer_response_factory(response, character, app):
    response['close'] = False
    response['#prepared-prayers'] = {
        'data': get_env(app).get_template(
            'character_prepared_prayers.html').render(
                prayers=PRAYERS, character=character)}
    response['#prayer-slots'] = {
        'data': get_env(app).get_template(
            'character_prayer_slots.html').render(character=character)}

def _power_validator(request, _):
    powers = []
    for power in POWERS:
        if power in request.POST:
            powers.append(power)
    return {'power_names': powers}

def _power_response_factory(response, character, app):
    response['#power-accordion'] = {
        'data': get_env(app).get_template(
            'character_powers_display.html').render(
                character=character, powers=POWERS),
        'activateTooltip': True}
    _skill_response_factory(response, character, app)

async def _inventory_validator(request, errors):
    action = request.match_info['extra']
    if action not in ['add', 'edit', 'increment', 'decrement', 'remove']:
        errors.append("invalid action")
        return {}
    try:
        name = ''.join(
            re.findall("[a-zA-Z0-9-_ ()]*", request.POST['name']))
        if action in ['add', 'edit']:
            amount = int(request.POST['amount'])
            extra = ''.join(
                re.findall("[a-zA-Z0-9-_ ()]*", request.POST['extra']))
            description = request.POST['description']
        if action == 'edit':
            new_name = ''.join(
                re.findall("[a-zA-Z0-9-_ ()]*", request.POST['new-name']))
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    except ValueError:
        errors.append("invalid value: only integers allowed")
    more_errors, _, character = await get_character(request)
    errors.extend(more_errors)
    if len(errors) != 0:
        return {}
    if action == 'add' and name in character['inventory']:
        errors.append("inventory item with that name already exists")
    elif action != 'add' and name not in character['inventory']:
        errors.append("no inventory item with name {}".format(name))
    if len(errors) != 0:
        return {}
    if action == 'add':
        character['inventory'][name] = {
            'amount': amount,
            'extra': extra,
            'description_unsafe': description}
    elif action == 'increment':
        character['inventory'][name]['amount'] += 1
    elif action == 'decrement':
        if character['inventory'][name]['amount'] < 1:
            errors.append("you cannot have less then zero items")
        else:
            character['inventory'][name]['amount'] -= 1
    elif action == 'remove':
        del character['inventory'][name]
    elif action == 'edit':
        del character['inventory'][name]
        character['inventory'][new_name] = {
            'amount': amount,
            'extra': extra,
            'description_unsafe': description}
    return {'inventory': character['inventory']}

def _inventory_response_factory(response, character, app):
    response['#inventory-accordion'] = {
        'data': get_env(app).get_template(
            'character_inventory_display.html').render(character=character)}

async def _coin_validator(request, errors):
    coins = {}
    try:
        for coin in COINS:
            coins[coin] = int(request.POST[coin])
    except ValueError:
        errors.append("invalid value: only integers allowed")
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    more_errors, _, character = await get_character(request)
    errors.extend(more_errors)
    oros = convert_coins(coins)
    if character['oros'] + oros < 0:
        errors.append("you can't spend money you don't have")
    return {'oros': character['oros'] + oros}

def _coin_response_factory(response, character, app):
    for coin in COINS:
        response['#{}-tooltip'.format(coin)] = {'activateTooltip': True}
    response['#coins'] = {
        'data': get_env(app).get_template(
            'character_coins.html').render(character=character, coins=COINS)}

async def _name_validator(request, errors):
    try:
        name = escape(request.POST['name'].strip())
    except KeyError as error:
        errors.append("missing value: {}".format(error))
    if name is not None and (len(name) < 1 or len(name) > 50):
        errors.append("length should be between one and fifty characters")
    if len(errors) == 0:
        characters = request.app['db'].characters
        if await characters.find_one(
                {'user_id': request['user']['_id'], 'name': name}) is not None:
            errors.append("you already have a character with this name")
    return {'name': name}

def _name_response_factory(response, character, _):
    response['#name-value'] = {'data': character['name']}
    response['title'] = {'data': "Dnd | {}".format(character['name'])}

async def _rest_validator(request, errors):
    more_errors, _, character = await get_character(request)
    errors.extend(more_errors)
    if len(errors) != 0:
        return {}
    for prayer in character['prepared_prayers']:
        character['prepared_prayers'][prayer]['cast'] = 0
    for spell in character['prepared_spells']:
        character['prepared_spells'][spell]['cast'] = 0
    return {
        'prepared_prayers': character['prepared_prayers'],
        'prepared_spells': character['prepared_spells']}

def _rest_response_factory(response, character, app):
    response['close'] = False
    _prepare_spell_response_factory(response, character, app)
    _prepare_prayer_response_factory(response, character, app)

def _background_validator(request, errors):
    field = request.match_info['extra']
    if field not in ['appearance', 'character', 'history']:
        errors.append('unknown field {}'.format(field))
    try:
        text = request.POST['text']
    except KeyError as error:
        errors.append("missing value: {}".format(error))
        return {}
    return {'{}_unsafe'.format(field): text}

def _background_response_factory(response, character, _):
    response['#appearance-value'] = {'data': character['appearance_safe']}
    response['#character-value'] = {'data': character['character_safe']}
    response['#history-value'] = {'data': character['history_safe']}
