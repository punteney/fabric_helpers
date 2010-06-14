import os

from fabric import state
from fabric.api import run, sudo
from fabric.contrib.files import append, exists, contains
from fabric_helpers.servers import Server

class MonitServer(Server):
    def __init__(self, name='monit', packages=['monit'],
            start_command='/etc/init.d/monit start',
            restart_command='/etc/init.d/monit restart',
            conf_files_path='/etc/monit/',
            conf_files=['monitrc'],
            **kwargs):
        kwargs['packages'] = packages
        kwargs['start_command'] = start_command
        kwargs['restart_command'] = restart_command
        kwargs['conf_files_path'] = conf_files_path
        kwargs['conf_files'] = conf_files
        super(MonitServer, self).__init__(name, **kwargs)
    
    def code_reload(self):
        pass

    def setup_config(self, **kwargs):
        # Setting up the main config file
        if exists('/etc/monit/monitrc'):
            sudo('rm /etc/monit/monitrc')
        sudo('cp %s /etc/monit/monitrc' % os.path.join(
                state.env.paths['live'], 'config/', self.name, 'monitrc'))
        
        #Setting up the individual service files
        services_path = os.path.join(state.env.paths['live'], 'config/', 
                                        self.name, 'services')
        if exists(services_path):
            dest_path = os.path.join(self.conf_files_path, 'monit.d')
            if not exists(dest_path):
                sudo('mkdir %s' % dest_path)
        
            sudo('cp %s/* %s/.' % (services_path, dest_path))
        
        # Have to change this file to be startup=1
        default_file = '/etc/default/monit'
        if contains('startup=0', default_file):
            sudo('rm %s' % default_file)
            sudo('touch %s' % default_file)
        append('startup=1', default_file, use_sudo=True)
        
   
        