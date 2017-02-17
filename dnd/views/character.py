"""Character page."""
from inspect import iscoroutinefunction
from bson import ObjectId
from aiohttp_login.decorators import restricted_api
from aiohttp.web import json_response
from markupsafe import escape
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
        'skill': (_skill_validator, _skill_response_factory),
        'name': (_name_validator, _name_response_factory),
        'background': (_background_validator, _background_response_factory),
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
    response = {'close': True}
    if iscoroutinefunction(response_factory):
        await response_factory(response, character)
    else:
        response_factory(response, character)
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
    _skill_response_factory(response, character)

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
    _skill_response_factory(response, character)
    _class_response_factory(response, character)

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
    _skill_response_factory(response, character)

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
    response['#class-points'] = {
        'data': character['unspent_class_points'],
        'addClass': ["label-danger"] if character[
            'unspent_class_points'] < 0 else ["label-default"],
        'removeClass': ["label-danger"] if character[
            'unspent_class_points'] >= 0 else ["label-default"]}
    response['#prayer-section'] = {
        'collapse': "show" if character['priest'] > 0 else "hide"}
    response['#spells-section'] = {
        'collapse': "show" if character['wizard'] > 0 else "hide"}
    response['#powers-section'] = {
        'collapse': "show" if character['warlock'] > 0 else "hide"}
    _skill_response_factory(response, character)

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

def _skill_validator(request, _):
    skills = []
    for skill in SKILLS:
        if skill in request.POST:
            skills.append(skill)
    return {'skill_names': skills}


def _skill_response_factory(response, character):
    response['#skill-accordion'] = {'data': '\n'.join(["""
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
          <a data-toggle="collapse" data-parent="#skill-accordion" href="#{}-collapse">{}</a>
      </h4>
    </div>
    <div id="{}-collapse" class="panel-collapse collapse">
      <div class="panel-body">
        {}
      </div>
    </div>
  </div>""".format(
      skill,
      skill,
      skill,
      character['skills'][skill]['description']) for skill in character['skills']])}
    response['#skill-points'] = {
        'data': character['unspent_skill_points'],
        'addClass': ["label-danger"] if character[
            'unspent_skill_points'] < 0 else ["label-default"],
        'removeClass': ["label-danger"] if character[
            'unspent_skill_points'] >= 0 else ["label-default"]}

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
                {'user': request['user'], 'name': name}) is not None:
            errors.append("you already have a character with this name")
    return {'name': name}

def _name_response_factory(response, character):
    response['#name-value'] = {'data': character['name']}
    response['title'] = {'data': "Dnd | {}".format(character['name'])}

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

def _background_response_factory(response, character):
    response['#appearance-value'] = {'data': character['appearance_safe']}
    response['#character-value'] = {'data': character['character_safe']}
    response['#history-value'] = {'data': character['history_safe']}
