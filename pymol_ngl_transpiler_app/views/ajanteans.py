from pyramid.view import view_config
from pyramid.renderers import render_to_response
import traceback
from PyMOL_to_NGL import PyMolTranspiler
from ..pages import Page
from ..models import User
import uuid
import shutil
import os
import io

#from pprint import PrettyPrinter
#pprint = PrettyPrinter()

def demo_file(request):
    """
    Needed for ajax_convert. Paranoid way to prevent user sending a spurious demo file name (e.g. ~/.ssh/).
    """
    demos=os.listdir(os.path.join('pymol_ngl_transpiler_app', 'demo'))
    if request.POST['demo_file'] in demos:
        return os.path.join('pymol_ngl_transpiler_app', 'demo', request.POST['demo_file'])
    else:
        raise Exception('Non existant demo file requested. Possible attack!')
def demo_file(request):
    """
    Needed for ajax_convert. Paranoid way to prevent user sending a spurious demo file name (e.g. ~/.ssh/).
    """
    demos=os.listdir(os.path.join('pymol_ngl_transpiler_app', 'demo'))
    if request.POST['demo_file'] in demos:
        return os.path.join('pymol_ngl_transpiler_app', 'demo', request.POST['demo_file'])
    else:
        raise Exception('Non existant demo file requested. Possible attack!')

def save_file(request, extension):
    filename=os.path.join('pymol_ngl_transpiler_app', 'temp','{0}.{1}'.format(uuid.uuid4(),extension))
    request.POST['file'].file.seek(0)
    with open(filename, 'wb') as output_file:
        shutil.copyfileobj(request.POST['file'].file, output_file)
    return filename



@view_config(route_name='ajax_convert', renderer="../templates/main.result.mako")
def ajax_convert(request):
    user = request.user
    try:
        minor_error=''
        ## assertions
        if not 'pdb_string' in request.POST and not request.POST['pdb']:
            return {'error': 'danger', 'error_title': 'No PDB code', 'error_msg': 'A PDB code is required to make the NGL viewer show a protein.','snippet':'','validation':''}
        elif request.POST['mode'] == 'out' and not request.POST['pymol_output']:
            return {'error': 'danger', 'error_title': 'No PyMOL code', 'error_msg': 'PyMOL code is required to make the NGL viewer show a protein.','snippet':'','validation':''}
        elif request.POST['mode'] == 'file' and not (('demo_file' in request.POST and request.POST['demo_file']) or ('file' in request.POST and request.POST['file'].filename)):
            return {'error': 'danger', 'error_title': 'No PSE file', 'error_msg': 'A PyMOL file to make the NGL viewer show a protein.','snippet':'','validation':''}

        ## convert booleans and settings
        def is_js_true(value): # booleans get converted into strings in json.
            if not value or value == 'false':
                return False
            else:
                return True
        settings = {'viewport': request.POST['viewport_id'],#'tabbed': int(request.POST['indent']),
                    'image': is_js_true(request.POST['image']),
                    'uniform_non_carbon':is_js_true(request.POST['uniform_non_carbon']),
                    'verbose': False,
                    'validation': True,
                    'stick': request.POST['stick'],
                    'save': request.POST['save'],
                    'backgroundcolor': 'white'}

        # parse data
        if request.POST['mode'] == 'out':
            view = ''
            reps = ''
            data = request.POST['pymol_output'].split('PyMOL>')
            for block in data:
                if 'get_view' in block:
                    view = block
                elif 'iterate' in block:  # strickly lowercase as it ends in _I_terate
                    reps = block
                elif not block:
                    pass  # empty line.
                else:
                    minor_error = 'Unknown block: ' + block
            trans = PyMolTranspiler(view=view, representation=reps, pdb=request.POST['pdb'], **settings)
            settings['loadfun'] = trans.get_loadfun_js(viewport=request.POST['viewport_id'], tag_wrapped=True)
        elif request.POST['mode'] == 'file':
            if 'demo_file' in request.POST:
                filename=demo_file(request) #prevention against attacks
            else:
                filename = save_file(request,'pse')
            trans = PyMolTranspiler(file=filename, **settings)
            request.session['file'] = filename
            if 'pdb_string' in request.POST:
                trans.raw_pdb = open(filename.replace('.pse','.pdb')).read()
            else:
                trans.pdb = request.POST['pdb']
        else:
            return {'snippet': 'Please stop trying to hack the server', 'error_title': 'A major error arose', 'error': 'danger', 'error_msg': 'The code failed to run serverside. Most likely malicius','viewport':settings['viewport']}
        # make output
        ###code = trans.get_html(ngl=request.POST['cdn'], **settings)
        code = 1
        pagename=str(uuid.uuid4())
        user.add_owned_page(pagename)
        request.dbsession.add(user)
        settings['author'] = [user.name]
        ##snippet_run=trans.code
        settings['loadfun'] = trans.get_loadfun_js(viewport=request.POST['viewport_id'])
        if trans.raw_pdb:
            settings['proteinJSON'] = '[{"type": "data", "value": "pdb", "isVariable": true, "loadFx": "loadfun"}]'
            settings['pdb'] = '\n'.join(trans.ss)+'\n'+trans.raw_pdb
        elif len(trans.pdb) == 4:
            settings['proteinJSON'] = '[{{"type": "rcsb", "value": "{0}", "loadFx": "loadfun"}}]'.format(trans.pdb)
        else:
            settings['proteinJSON'] = '[{{"type": "file", "value": "{0}", "loadFx": "loadfun"}}]'.format(trans.pdb)
        # sharable page
        settings['editors'] = [user.name]
        Page(pagename).save(settings)
        if minor_error:
            return {'snippet': True, 'error': 'warning', 'error_msg':minor_error, 'error_title':'A minor error arose','validation':trans.validation_text, 'page': pagename, **settings}
        else:
            return {'snippet': True, 'validation':trans.validation_text, 'page': pagename, **settings}

    except:
        print('**************')
        print(traceback.format_exc())
        return {'snippet': False,'error_title':'A major error arose', 'error': 'danger','error_msg':'The code failed to run serverside:<br/><pre><code>'+traceback.format_exc()+'</code></pre>','validation':''}

@view_config(route_name='ajax_custom', renderer="../templates/custom.result.mako")
def ajax_custom(request):
    if 'demo_file' in request.POST:
        filename = demo_file(request)  # prevention against attacks
        fh = open(filename)
    else:
        request.POST['file'].file.seek(0)
        fh = io.StringIO(request.POST['file'].file.read().decode("utf8"), newline=None)
    mesh = []
    o_name = ''
    scale_factor = 0
    vertices = []
    trilist = []
    sum_centroid = [0,0,0]
    min_size = [0,0,0]
    max_size = [0,0,0]
    centroid = [0, 0, 0]
    for row in fh:
        if row[0] == 'o':
            if o_name:
                mesh.append({'o_name':o_name,'triangles':trilist})
                vertices = []
                trilist = []
                scale_factor = 0
                sum_centroid = [0,0,0]
                min_size = [0,0,0]
                max_size = [0,0,0]
            o_name = row.rstrip().replace('o ','')
        elif row[0] == 'v':
            vertex = [float(e) for e in row.split()[1:]]
            vertices.append(vertex)
            for ax in range(3):
                sum_centroid[ax] += vertex[ax]
                min_size[ax] = min(min_size[ax], vertex[ax])
                max_size[ax] = max(max_size[ax], vertex[ax])
        elif row[0] == 'f':
            if scale_factor == 0: #first face.27.7  24.5
                # euclid = sum([(max_size[ax]-min_size[ax])**2 for ax in range(3)])**0.5
                scale_factor = float(request.POST['scale']) / max([abs(max_size[ax] - min_size[ax]) for ax in range(3)])
                if request.POST['centroid'] == 'origin':
                    centroid = [sum_centroid[ax]/len(vertices) for ax in range(3)]
                elif request.POST['centroid'] == 'unaltered':
                    centroid = [0, 0, 0]
                elif request.POST['centroid'] == 'custom':
                    origin = request.POST['origin'].split(',')
                    centroid = [sum_centroid[ax] / len(vertices) - float(origin[ax])/scale_factor  for ax in range(3)]  #the user gives scaled origin!
                else:
                    raise ValueError('Invalid request')

            new_face = [e.split('/')[0] for e in row.split()[1:]]
            if (len(new_face) != 3):
                pass
            trilist.extend([int((vertices[int(i) - 1][ax]-centroid[ax])*scale_factor*100)/100 for i in new_face[0:3] for ax in range(3)])
    mesh.append({'o_name': o_name, 'triangles': trilist})
    return {'mesh': mesh}

@view_config(route_name='ajax_pdb', renderer="../templates/main.result.mako")
def ajax_pdb(request):
    pagename = str(uuid.uuid4())
    settings = {'data_other': request.POST['viewcode'].replace('<div', '').replace('</div>', '').replace('<', '').replace('>', ''),
                'backgroundcolor': 'white', 'validation': None, 'js': None, 'pdb': '', 'loadfun': ''}
    if request.POST['mode'] == 'code':
        if len(request.POST['pdb']) == 4:
            settings['proteinJSON'] = '[{{"type": "rcsb", "value": "{0}"}}]'.format(request.POST['pdb'])
        else:
            settings['proteinJSON'] = '[{{"type": "file", "value": "{0}"}}]'.format(request.POST['pdb'])
    else:
        settings['proteinJSON'] = '[{"type": "data", "value": "pdb", "isVariable": true}]'
        filename = save_file(request,'pdb')
        trans = PyMolTranspiler.load_pdb(file=filename)
        settings['pdb'] = '\n'.join(trans.ss) + '\n' + trans.raw_pdb
        settings['js'] = 'external'
        #make_static_js(**settings)
    Page(pagename).save(settings)
    #make_static_html(**settings)
    return {'snippet': True, **settings}

@view_config(route_name='edit_user-page', renderer='json')
def edit(request):
    # get ready
    page = Page(request.POST['page'])
    user = request.user
    ownership = user.owned_pages.split(' ')
    ## cehck permissions
    if page.identifier not in ownership: ## only owners can edit.
        request.response.status = 404
        return render_to_response("../templates/404.mako", {'project': 'Michelanglo', 'user': request.user}, request)
    else:
        #load data
        settings = page.load()
        if not settings:
            request.response.status = 404
            return render_to_response("../templates/404.mako", {'project': 'Michelanglo', 'user': request.user}, request)
        #add author if user was an upgraded to editor by the original author
        if user.name not in settings['author']:
            settings['author'].append(user.name)
        # only admins and friends can edit html fully
        if user.role in ('admin', 'friend'):
            for key in ('loadfun', 'title', 'description'):
                if key in request.POST:
                    settings[key] = request.POST[key]
        else: # regular users have to be sanitised
            for key in ('title', 'description'):
                if key in request.POST:
                    settings[key] = Page.sanitise_HTML(request.POST[key])
        #save
        Page(request.POST['page']).save(settings)
        return {'success': 1}


@view_config(route_name='delete_user-page', renderer='json')
def delete(request):
    # get ready
    page = Page(request.POST['page'])
    user = request.user
    ownership = user.get_owned_pages()
    ## cehck permissions
    if page.identifier not in ownership: ## only owners can delete
        request.response.status = 403
        return {'status': 'Not owner'}
    else:
        page.delete()
        return {'status': 'success'}


@view_config(route_name='get')
def get_ajax(request):
    user = request.user
    if request.POST['item'] == 'pages':
        if not user:
            request.response.status = 403
            return render_to_response("../templates/404.mako", {'project': 'Michelanglo', 'user': request.user}, request)
        elif user.role == 'admin':
            target = request.dbsession.query(User).filter_by(name=request.POST['username']).one()
            return render_to_response("../templates/login/pages.mako", {'project': 'Michelanglo', 'user': target}, request)
        elif request.POST['username'] == user.name:
            return render_to_response("../templates/login/pages.mako", {'project': 'Michelanglo', 'user': request.user}, request)
        else:
            request.response.status = 403
            return render_to_response("../templates/404.mako", {'project': 'Michelanglo', 'user': request.user}, request)
