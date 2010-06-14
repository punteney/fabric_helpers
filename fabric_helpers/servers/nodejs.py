from __future__ import with_statement
import os

from fabric import state
from fabric.api import run, sudo, cd, local
from fabric.contrib.files import exists
from warnings import warn

from fabric_helpers.servers import Server


class NodeServer(Server):
    def __init__(self, name='node', version='0.1.98', 
            packages=['upstart', 'build-essential', 'git-core',],
            conf_files_path='/etc/init/', **kwargs):
        
        self.version = version
        self.download_path = 'http://nodejs.org/dist/node-v%s.tar.gz' % version

        kwargs['packages'] = packages
        kwargs['conf_files_path'] = conf_files_path
        super(NodeServer, self).__init__(name, **kwargs)

    def install(self):
        self.install_node()
        self.install_kiwi()

    def start(self):
        if self.conf_files:
            for conf_file in self.conf_files:
                service = conf_file[:-5]
                if self.service_running(service):
                    sudo('restart %s' % service)
                else:
                    sudo('start %s' % service)
        else:
            print "No Node Servers specified to start"

    def restart(self):
        if self.conf_files:
            for conf_file in self.conf_files:
                service = conf_file[:-5]
                if self.service_running(service):
                    sudo('restart %s' % service)
                else:
                    sudo('start %s' % service)
        else:
            print "No Node Servers specified to restart"

    def service_running(self, service):
        status = sudo('status %s' % service)
        if status.find('running') > 0:
            return True
        else:
            return False

    def setup_config(self, project_conf_dir=None, server_type=None):
        # Node conf files are actually upstart conf files for starting/stopping
        # the node server daemon
        if self.conf_files:
            if not server_type:
                server_type=state.env.name
            if not project_conf_dir:
                project_conf_dir = os.path.join(state.env.paths['live'], 'config/')

            for conf_file in self.conf_files:
                new_file = os.path.join(project_conf_dir, self.name, server_type, conf_file)
                
                if not exists(new_file):
                    #No specific config file for the deployment env (prod, staging, etc) so use the general one
                    new_file = os.path.join(project_conf_dir, self.name, conf_file)
                if exists(new_file):
                    conf_path = os.path.join(self.conf_files_path, conf_file)
                    sudo('cp %s %s' % (new_file, conf_path))
        
        #Creating the logfile
        sudo('touch /var/log/node.log')
        sudo('chown www-data /var/log/node.log')
    
        
    def install_node(self):
        if not exists('node-v%s.tar.gz' % self.version):
            run('curl -O %s' % self.download_path)
            run('tar -xvzf node-v%s.tar.gz' % self.version)
        
        with cd('node-v%s' % self.version):
            run('./configure')
            run('make')
            sudo('make install')          
    
    def install_kiwi(self):
        if not exists('kiwi'):
            run('git clone http://github.com/visionmedia/kiwi.git')
        with cd('kiwi'):
            run('git pull')
            sudo('make install')

    
