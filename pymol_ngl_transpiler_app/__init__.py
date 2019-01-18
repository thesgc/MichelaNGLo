from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    my_session_factory = SignedCookieSessionFactory('TIM barrels')
    config.set_session_factory(my_session_factory)
    config.include('pyramid_mako')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('user-structures', 'user', cache_max_age=3600)
    config.add_static_view('images', '../images', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('ajax_convert', '/ajax_convert')
    config.add_route('save_pdb', '/save_pdb')
    config.scan()
    return config.make_wsgi_app()
