import os
import time
from fabric import state
from fabric.api import run, sudo, cd, local
from fabric.contrib.files import exists, append
from warnings import warn


class Machines(object):
    def __init__(self, machines=[]):
        self.machines = machines
        self.env_dicts = {}
    
    def get_by_env(self, env_name):
        return self._filter_by_value('env_name', env_name)
    
    def get_by_host(self, host):
        return self._filter_by_value('public_address', host)[0]
    
    def get_connections_for_env(self, env_name):
        selected_machines = self.get_by_env(env_name)
        hosts = []
        for m in selected_machines:
            hosts.append(m.ssh_connection_string())
        return hosts
    
    def _filter_by_value(self, key, value):
        selected = []
        for m in self.machines:
            if getattr(m, key, None) == value:
                selected.append(m)
        return selected

    def register(self, machine):
        self.machines.append(machine)

class Machine(object):
    def __init__(self, public_address, env_name, short_name=None, private_address=None, 
            base_server=None, servers=[], python_version='2.6', ssh_port=22):
        self.public_address = public_address
        self.env_name = env_name
        self.private_address = private_address
        if base_server:
            self.base_server = base_server
        else:
            self.base_server = BaseUbuntuMachine(ssh_port=ssh_port)
        self.servers = servers
        self.python_version='2.6'
        self.ssh_port=ssh_port
    
    def add_server(self, server):
        self.servers.append(server)

    # Return the ssh connection string
    def ssh_connection_string(self, server_address=None):
        if not server_address:
            server_address = self.public_address
        return '%s:%i' % (server_address, self.ssh_port)
    
    # Return the ssh connection string for the internal address
    #   only_internal - If True will through a "ValueError" exception if the
    #       machine doesn't have a private address. If False the public 
    #       address will be used if the machine doesn't have a private 
    #       address
    def ssh_connection_string_internal(self, only_internal=False):
        if self.private_address:
            return self.ssh_connection_string(self.private_address)
        elif not only_internal:
            # Use the public_address
            return self.ssh_connection_string()
        else:
            raise ValueError('This server does not have a private address')
    
    def install(self):
        self.base_server.install()

    def install_servers(self):
        for s in self.servers:
            s.install()
        
    def copy_ssh_keys(self, server_user):
        # If a project user is specified we are running as root and but 
        # we want to copy the keys for the project user, if no than it's not 
        # root and we pull the normal user.
        local('ssh-copy-id %s@%s' % (server_user, self.public_address))
            
class BaseUbuntuMachine(object):
    def __init__(self, type='Ubuntu', packages=[
                'ufw',
                'build-essential',
                'python-setuptools',
                'git-core',
                'subversion',
                'mercurial',
                'postgresql-client',
                'python-imaging',
                'python-psycopg2',
                'python-dev',
                'wv', 
                'ghostscript',
                'libpng3', 
                'libjpeg62', 
                'texlive', 
                'faad',
                'ffmpeg',
                'imagemagick',
            ], ssh_port=22, locale='en_US.UTF-8'):
        self.type = type
        self.packages = packages
        self.ssh_port = ssh_port
        self.locale = locale
    
    def install(self):
        self.set_locale()
        self.update_packages()
        self.install_packages()

    def set_locale(self):
        sudo('locale-gen %s' % self.locale)
        sudo('/usr/sbin/update-locale LANG=%s' % self.locale)
    
    # Update all installed packages to current version
    def update_packages(self):
        sudo('aptitude -y update')
        sudo('aptitude -y safe-upgrade')
        sudo('aptitude -y full-upgrade')
        
    def install_packages(self):
        if self.packages:
            sudo('aptitude -y install %s' % " ".join(self.packages))

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

    def code_reload(self):
        self.restart()
    
    def install(self):
        self.install_packages()
        self.setup()
        self.restart()
        
    def install_packages(self):
        if self.packages:
            sudo('aptitude -y install %s' % " ".join(self.packages))

    def setup(self):
        self.setup_config_files()
        
    def setup_config_files(self, project_conf_dir=None, server_type=None):
        if self.conf_files:
            if not server_type:
                server_type=state.env.name
            if not project_conf_dir:
                project_conf_dir = os.path.join(state.env.paths['live'], 'config/')
        
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
                warn("**** NO '%s' SITE CONFIG for %s ****" % (site, self.name))

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

class PostgresqlServer(Server):
    def __init__(self, name="postgresql", packages=['postgresql','postgresql-dev'], 
            start_command='invoke-rc.d postgresql-8.4 start',
            restart_command='invoke-rc.d postgresql-8.4 restart',
            conf_files_path='/etc/postgresql/8.4/main/',
            conf_files=['pg_hba.conf', 'postgresql.conf'],
            **kwargs):

        super(PostgresqlServer, self).__init__(name, packages=packages, 
            start_command=start_command, 
            restart_command=restart_command, 
            conf_files_path=conf_files_path,
            conf_files=conf_files,
            **kwargs)
    
    def code_reload(self):
        pass

    def setup(self):
        self.setup_config_files()
        # self.create_db()
    
    # def create_db(self):
    #   Currently requires user input, need to determine how to create these without needing user input
    #     run('sudo -u postgres createuser %s' % state.env.DATABASE_USER)
    #     run('sudo -u postgres createdb -O %s %s' % (state.env.DATABASE_USER, state.env.DATABASE_NAME))

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
        run('mkdir %s' % os.path.join(state.env.paths['root'], 'celery'))
        sudo('ln %s /etc/init.d/celeryd') % (os.path.join(state.env.paths['live'], 'config/init_scripts/celeryd'))
        sudo('chmod +x /etc/init.d/celeryd')
        sudo('update-rc.d celeryd defaults')

