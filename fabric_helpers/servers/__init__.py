import os
import time

from fabric import state
from fabric.api import run, sudo, cd, local
from fabric.contrib.files import exists

class Server(object):
    def __init__(self, name, conf_files_path=None, conf_files=[], 
                    packages=[], pip_packages=[], restart_command=None, 
                    start_command=None):
        self.name = name
        if conf_files_path:
            self.conf_files_path = conf_files_path
        else:
            self.conf_files_path = os.path.join('/etc', name)
        self.conf_files = conf_files
        self.packages=packages
        self.pip_packages = pip_packages
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
            print self.name
            raise NotImplementedError, "Restart command wasn't specified for this server"
        else:
            sudo(self.restart_command)

    def code_reload(self):
        # When the code is changed does what should the server do to start 
        # using the new code
        self.restart()
    
    def install(self):
        pass

    def setup(self):
        self.setup_config()
        self.restart()

    def after_project_setup(self):
        # Put any setup that requires the project files to be present here.
        pass
        
    def setup_config(self, project_conf_dir=None, server_type=None):
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
  