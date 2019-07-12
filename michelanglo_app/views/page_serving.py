from pyramid.view import view_config
from pyramid.renderers import render_to_response
from ..models.pages import Page

import logging, json
log = logging.getLogger(__name__)
from ._common_methods import get_username

@view_config(route_name='userdata', renderer="../templates/user_protein.mako")
def userdata_view(request):

    def tickup_tries(): #try counter for encryption. currently doesn't have a time out because I am not sure w
        if 'tries' in request.session:
            request.session['tries'] = int(request.session['tries']) + 1
        else:
            request.session['tries'] = 0  ## first go

    log.info(f'{get_username(request)} is looking at a page')
    pagename = request.matchdict['id']
    page = Page(pagename)
    if not page.exists(True):
        response_settings = {'project': 'Michelanglo', 'user': request.user, 'page': pagename}
        return render_to_response("../templates/410.mako", response_settings, request)
    ### deal with encryption
    if page.is_password_protected() and 'key' in request.params: # encrypted and key given
        page.key = request.params['key'].encode('utf-8')
        page.path = page.encrypted_path
        try:
            settings = page.load()
            settings['encryption'] = True
            settings['encryption_key'] = request.params['key']
        except ValueError: ##got it wrong
            log.warn('f{get_username(request)} got the password wrong.')
            tickup_tries()
            response_settings = {'project': 'Michelanglo', 'user': request.user, 'tries': request.session['tries'], 'page': pagename}
            return render_to_response("../templates/encrypted.mako", response_settings, request)
    elif page.is_password_protected() and 'key' not in request.params:  # encrypted and no key given
        tickup_tries()
        response_settings = {'project': 'Michelanglo', 'user': request.user, 'tries': request.session['tries'], 'page': pagename}
        return render_to_response("../templates/encrypted.mako", response_settings, request)
    else:
        settings = page.load()
        settings['encryption'] = False
    ### add new values
    if 'freelyeditable' not in settings:
        settings['freelyeditable'] = False
    settings['user'] = request.user
    user = request.user
    if user:
        if settings['freelyeditable']:
            settings['editable'] = True
            user.add_visited_page(pagename)
            settings['visitors'].append(user.name)
        elif user.role == 'admin':
            # this means admin does not leave a trace upon inspection. Fine for admin bots. Bad human admin.
            settings['editable'] = True
        elif pagename in user.get_owned_pages():
            settings['editable'] = True
        elif pagename in user.get_visited_pages():
            settings['editable'] = False
        else:
            user.add_visited_page(pagename)
            request.dbsession.add(user)
            settings['visitors'].append(user.name)
            page.save()
            settings['editable'] = False
    else:
        settings['editable'] = False
    ### extras?
    if 'remote' in request.params:
        settings['remote'] = True
    if 'bootstrap' in request.params:
        settings['bootstrap'] = request.params['bootstrap']
    if 'no_user'  in request.params:
        settings['no_user'] = True
    else:
        settings['no_user'] = False
    if 'no_buttons' in request.params:
        settings['no_buttons'] = True
    else:
        settings['no_buttons'] = False
    settings['no_analytics'] = True
    if not 'columns_viewport' in settings:
        settings['columns_viewport'] = 9
        settings['columns_text'] = 3
    if not 'location_viewport' in settings:
        settings['location_viewport'] = 'left'
    settings['current_page'] = 'NOT A MENU OPTION....'
    #API hack.
    if 'mode' in request.params and request.params['mode'] == 'json':
        settings['user'] = get_username(request) #user isn't json serialisable
        #print('pageserve', 'request', type(settings['proteinJSON']))
        settings['proteinJSON'] = settings['proteinJSON'] #json.dumps() #because this is done badly.
        return render_to_response("json", settings, request)
    return settings



@view_config(route_name='save_pdb', renderer='string')
def save_pdb(request):
    page = Page(request.params['uuid'])
    if 'key' in request.params:
        page.key = request.params['key'].encode('utf-8')
    return page.load()['pdb']



@view_config(route_name='save_zip', renderer="string")
def save_zip(request):
    raise NotImplementedError

