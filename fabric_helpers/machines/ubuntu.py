from fabric.api import run, sudo, cd, local

from fabric_helpers.machines import Machine

class UbuntuServer(Machine):
    def __init__(self, 
            public_address, 
            env_name, 
            open_ports=[], 
            private_address=None, 
            private_ports=[],
            servers=[], 
            python_version='2.6', 
            ssh_port=22,
            locale='en_US.UTF-8',
            packages=[
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
            ],
        ):

        self.public_address = public_address
        self.env_name = env_name
        self.open_ports = open_ports
        self.private_address = private_address
        self.private_ports = private_ports
        self.servers = servers
        self.ssh_port = ssh_port
        self.locale = locale
        self.packages = packages
        self.python_version='2.6'
        self.ssh_port = ssh_port
    
    def install(self):
        self.set_locale()
        self.setup_firewall()
        self.update_packages()
        self.install_packages()
        self.install_servers()

    def set_locale(self):
        sudo('locale-gen %s' % self.locale)
        sudo('/usr/sbin/update-locale LANG=%s' % self.locale)
    
    def setup_firewall(self):
        sudo('aptitude -y install ufw')
        sudo('ufw default deny')
        sudo('ufw allow %s' % self.ssh_port)
        for port in self.open_ports:
            sudo('ufw allow %s' % port)
        if self.private_address and self.private_ports:
            for port in self.private_ports:
                sudo('ufw allow to %s port %s' % (self.private_address, port))
        sudo("echo 'y' | ufw enable")
        
    # Update all installed packages to current version
    def update_packages(self):
        sudo('aptitude -y update')
        sudo('aptitude -y safe-upgrade')
        sudo('aptitude -y full-upgrade')
        
    def install_packages(self, packages=None):
        if not packages:
            packages = self.packages
            sudo('aptitude -y install %s' % " ".join(self.packages))