from fabric.api import run, sudo, cd, local

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
    def __init__(self, public_address, env_name, 
            open_ports=[], private_address=None, private_ports=[],
            base_server=None, servers=[], python_version='2.6', ssh_port=22):
        self.public_address = public_address
        self.env_name = env_name
        self.private_address = private_address
        if base_server:
            self.base_server = base_server
        else:
            self.base_server = BaseUbuntuMachine(
                                        ssh_port=ssh_port, 
                                        open_ports=open_ports,
                                        private_address=private_address,
                                        private_ports=private_ports,
                                )
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
        raise NotImplementedError, "Install isn't defined for this machine"

    def install_servers(self):
        for s in self.servers:
            s.install()
    
    def get_pip_packages(self):
        packages = []
        for s in self.servers:
            for p in s.pip_packages:
                packages.append(p)
        return packages
        
    def copy_ssh_keys(self, server_user):
        # If a project user is specified we are running as root and but 
        # we want to copy the keys for the project user, if no than it's not 
        # root and we pull the normal user.
        local('ssh-copy-id %s@%s' % (server_user, self.public_address))

    def install_packages(self, packages=None):
        raise NotImplementedError, "Install packages command wasn't defined for this machine"







