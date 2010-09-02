import os

from fabric import state
from fabric.api import run, sudo, cd, local
from fabric.contrib.files import exists
from warnings import warn

from fabric_helpers.servers import Server

class WebServer(Server):
    def __init__(self, name, sites_enabled_path, default_site, sites, **kwargs):
        self.name = name
        self.sites_enabled_path = sites_enabled_path
        self.default_site = default_site
        self.sites = sites

        super(WebServer, self).__init__(name, **kwargs)

    def site_config_dir(self):
        return os.path.join(state.env.paths['config'], self.name, state.env.name)

    def enable_sites(self):
        for site in self.sites:
            if site[-5:] != '.conf':
                site = site + '.conf'
            if exists(os.path.join(self.site_config_dir(), site)):
                self.disable_site(site) # Get rid of the old site if it exists
                self.enable_site(site)
            else:
                warn("**** NO '%s' SITE CONFIG for %s at %s ****" % (site, self.name, os.path.join(self.site_config_dir(), site)))

    def enable_site(self, site):
        sudo('ln -s %s %s/%s' % 
              (os.path.join(self.site_config_dir(), site), self.sites_enabled_path, site))

    def disable_site(self, site):
        if exists('%s/%s' % (self.sites_enabled_path, site)):
            sudo('rm %s/%s' % (self.sites_enabled_path, site))

    def setup(self, *args, **kwargs):
        super(WebServer, self).setup(*args, **kwargs)
        self.enable_sites()
        self.deactivate_default()

    def deactivate_default(self):
        # Deactivate the default site
        self.disable_site(self.default_site)
                
class ApacheServer(WebServer):
    def __init__(self, name='apache', sites=[], 
            sites_enabled_path='/etc/apache2/sites-enabled', 
            default_site='000-default', 
            conf_files_path='/etc/apache2',
            conf_files = ['apache2.conf', 'ports.conf'], 
            packages=[
                'apache2', 
                'apache2.2-common', 
                'apache2-mpm-prefork', 
                'apache2-utils', 
                'libexpat1', 
                'ssl-cert', 
                'libapache2-mod-wsgi'
            ],
            restart_command='apache2ctl graceful',
            start_command='apache2ctl start', **kwargs
        ):

        super(ApacheServer, self).__init__(name,
            sites_enabled_path,
            default_site,
            sites,
            conf_files_path=conf_files_path,
            conf_files=conf_files,
            packages=packages,
            restart_command=restart_command,
            start_command=start_command,
            **kwargs)
        
    def wsgi_dir(self):
        return os.path.join(state.env.paths['config'], 'wsgi', state.env.name)
        
    def code_reload(self):
        wsgi_dir = self.wsgi_dir()
        listing = run('ls %s' % (wsgi_dir))
        wsgi_list = listing.split('\n')
        for w_file in wsgi_list:
            if w_file != '':
                run('touch %s' % os.path.join(wsgi_dir, w_file))

class NginxServer(WebServer):
    def __init__(self, 
            name='nginx', 
            sites=[], 
            sites_enabled_path='/etc/nginx/sites-enabled', 
            default_site='default', 
            conf_files_path='/etc/nginx',
            conf_files = ['nginx.conf'],
            packages=['nginx'],
            restart_command='/etc/init.d/nginx restart',
            start_command='/etc/init.d/nginx start', 
            **kwargs
        ):

        super(NginxServer, self).__init__(name,
            sites_enabled_path,
            default_site,
            sites,
            conf_files_path=conf_files_path,
            conf_files=conf_files,
            packages=packages,
            restart_command=restart_command,
            start_command=start_command,
            **kwargs)
    
    def code_reload(self):
        pass
