import os
from fabric import state
from fabric.api import hosts, run, sudo, cd
from fabric.contrib.files import exists, append


class Machines(object):
    def __init__(self, machines):
        self.machines = machines
        self.env_dicts = {}
    
    def for_env(self, env_name):
        if env_name not in Machines.env_dicts:
            Machines.env_dicts[env_name] = []
            for host, machine in Machines.machines.items():
                if machine['env_name'] == env_name:
                    if 'port' in machine:
                        Machines.env_dicts[env_name].append(host+':'+machine['port'])
                    else:
                        Machines.env_dicts[env_name].append(host)
        return self.env_dicts[env_name]
    
    def get(self, key):
        return self.machines[key]




class Server(object):
    def __init__(self, name, conf_files_path=None, conf_files=[], 
                    packages=[], restart_command=None, start_command=None):
        self.name = name
        if conf_files_path:
            self.conf_files_path = conf_files_path
        else:
            self.conf_files_path = os.path.join('/etc', name)
        self.conf_files = conf_files
        self.packages=packages
        self.restart_command = restart_command
        if start_command == None:
            self.start_command = self.restart_command
        else:
            self.start_command = start_command

    def start(self):
        if not self.start_command:
            # If the server doesn't need a restart just override this as pass
            raise NotImplementedError, "Start command wasn't specified for this server"
        else:
            sudo(self.start_command)
    
    def restart(self):
        if not self.restart_command:
            # If the server doesn't need a restart just override this as pass
            raise NotImplementedError, "Restart command wasn't specified for this server"
        else:
            sudo(self.restart_command)

    def quick_reload(self):
        self.restart()
    
    def install(self):
        if self.packages:
            sudo('aptitude -y install %s' % " ".join(self.packages))

    def setup_config(self):
        self.setup_config_files()
        
    def setup_config_files(self, project_conf_dir=None, server_type=None):
        if self.conf_files:
            if not server_type:
                server_type=state.env.name
            if not project_conf_dir:
                project_conf_dir = os.path.join(state.env.project_paths['live'], state.env.project_name, 'config/')
        
            timestamp = time.strftime('%Y%m%d%H%M%S')
            for conf_file in self.conf_files:
                new_file = os.path.join(project_conf_dir, self.name, server_type, conf_file)
                if not exists(new_file):
                    #No specific config file for the deployment env (prod, staging, etc) so use the general one
                    new_file = os.path.join(project_conf_dir, self.name, conf_file)
                if exists(new_file):
                    conf_path = os.path.join(self.conf_files_path, conf_file)
                    if exists(conf_path):
                        sudo('mv %s %s-%s.bak' % (conf_path, conf_path, timestamp))
                    sudo('ln -s %s %s' % (new_file, conf_path))
  
class WebServer(Server):
    def __init__(self, name, sites_enabled_path, default_site, sites, **kwargs):
        self.sites_enabled_path = sites_enabled_path
        self.default_site = default_site
        self.sites = sites
        super(WebServer, self).__init__(name, **kwargs)

    def enable_sites(self):
        for site in self.sites:
            if exists('%s/config/%s/%s/%s' % 
                (state.env.project_path, self.name, state.env.name, site)):
                self.disable_site(site) # Get rid of the old site if it exists
                self.enable_site(site)
            else:
                warn("**** NO '%s' SITE CONFIG for %s ****" % (site, self.name))

    def enable_site(self, site):
        sudo('ln -s %s/config/%s/%s/%s %s/%s' % 
              (state.env.project_path, self.name, state.env.name, site, self.sites_enabled_path, site))

    def quick_reload(self):
        pass

    def disable_site(self, site):
        if exists('%s/%s' % (self.sites_enabled_path, site)):
            sudo('rm %s/%s' % (self.sites_enabled_path, site))

    def deactivate_default(self):
        # Deactivate the default site
        self.disable_site(self.default_site)
                
class ApacheServer(WebServer):
    def __init__(self, name, sites=[], 
        sites_enabled_path='/etc/apache2/sites-enabled', default_site='default', 
        conf_files_path='/etc/apache2', 
        packages=['apache2', 'apache2.2-common', 'apache2-mpm-prefork', 'apache2-utils', 'libexpat1', 'ssl-cert', 'libapache2-mod-wsgi'],
        restart_command='apache2ctl graceful',
        start_command='apache2ctl start', **kwargs):

        super(ApacheServer, self).__init__(name, **kwargs)
        
    def wsgi_dir(self):
        return '%s/wsgi_handlers' % state.env.project_paths['live']
        
    def quick_reload(self):
        wsgi_dir = self.wsgi_dir()
        listing = run('ls %s' % (wsgi_dir))
        wsgi_list = listing.split('\n')
        for w_file in wsgi_list:
            if w_file != '':
                run('touch %s' % os.path.join(wsgi_dir, w_file))

class NginxServer(Webserver):
    def __init__(self, name, sites=[], 
            sites_enabled_path='/etc/nginx/sites-enabled', default_site='default', 
            conf_files_path='/etc/nginx', packages=['nginx'],
            restart_command='/etc/init.d/nginx reload',
            start_command='/etc/init.d/nginx start', **kwargs):

        super(NGINXServer, self).__init__(name, **kwargs)



class RabbitServer(Server):
    def __init__(self, name, packages=['rabbitmq-server'],
            start_command='/etc/init.d/rabbitmq-server start', **kwargs):
        # restart_command='/etc/init.d/rabbitmq-server restart'
        
        super(RabbitServer, self).__init__(name, **kwargs)

    def setup_config(self):
        sudo("rabbitmqctl add_user %s rabbitpass" % state.env.user)
        sudo("rabbitmqctl add_vhost %s" % state.env.project_name)
        sudo('rabbitmqctl map_user_vhost %s gr_select' % state.env.user)
        
    def restart(self):
        # Rabbitmq shouldn't need to be restarted on updates
        # Do need to add in functionality to restart the celery process
        pass


class CeleryServer(Server):
    def __init__(self, name, packages=['rabbitmq-server'],
            start_command='/etc/init.d/celeryd start', 
            restart_command='/etc/init.d/celeryd restart', **kwargs):
        # restart_command='/etc/init.d/rabbitmq-server restart'
        
        super(CeleryServer, self).__init__(name, **kwargs)


    def setup_config(self):
        run('mkdir %s' % os.path.join(state.env.project_paths['root'], 'celery'))
        sudo('ln %s /etc/init.d/celeryd') % (os.path.join(state.env.project_paths['live'], 'config/init_scripts/celeryd'))
        sudo('chmod +x /etc/init.d/celeryd')
        sudo('update-rc.d celeryd defaults')

