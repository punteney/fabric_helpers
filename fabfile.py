from fabric_helpers import *
from fabric_helpers.machines import Machines 
from fabric_helpers.machines.ubuntu import UbuntuServer
from fabric_helpers.servers.db import PostgresqlServer
from fabric_helpers.servers.web import NginxServer, ApacheServer
from fabric_helpers.servers.queue import RabbitServer, CeleryServer

# A "Machine" is a representation of an actual system the 'physical server'
# A "Server" is a representation of a specific server software to be installed
# on the Machine. Things like Postgres, Apache, etc.


# The user on the machine, this should be a generic user (ie not a real 
# individual) or a user that is specific to this project.
USER = 'zoo'

# The default Postgres sever configuration
POSTGRES = PostgresqlServer()

# The default Apache and nginx server configuration with a site called 
# "django_site" this is used for setting the conf files and enabling the site.
APACHE = ApacheServer(sites=['django_site'])
NGINX = NginxServer(sites=['django_site'])



# Registering individual machines
# This is the default setup for a single machine with nginx proxying to apache
# with a postgres DB backend.
# Update the IP/Hostname to match your server
MACHINES = Machines([
    UbuntuServer('173.203.82.75', 
        ENVIRONMENTS['production'], 
        servers=[POSTGRES, APACHE, NGINX, RabbitServer(), CeleryServer()],
        open_ports=[80, 443], # http, ssl, ssh
        private_ports=[5672,], # rabbitmq
        private_address='10.179.73.220',
    ),

#   Uncomment the following lines for a matching staging server
#    Machine('SERVER IP OR HOSTNAME HERE', ENVIRONMENTS['staging'], 
#        short_name="prod", servers=[POSTGRES, APACHE, NGINX]),
])

# This will be the folder that all of the project files are kept in.
env.project_name = 'zoo_site'

# The name and location of your project folder. By default it's set to:
# /home/USERNAME/PROJECTNAME 
env.project_root = os.path.join('/home/', USER, env.project_name)

# The name of the actual project folder within the project_root defined above
# Can leave as none if you the project isn't in a subfolder. This is the 
# folder that holds the settings.py and other standard project files
env.project_folder_name = None

# The path to your git repo ie:
# env.git_repo = 'git://github.com/punteney/fab_helpers.git'
env.git_repo = 'git://github.com/punteney/tutorial_zoo_site.git'

# The git branch to push. 
# By default it will push the currently checked out branch, but you can 
# uncomment below to have it push a specific branch even if that isn't 
# currently checked out.
# env.git_branch = 'master'

# If you only want a specific branch to be able to be pushed to production 
# specify that here. This can be used as a safety net to make sure a dev 
# branch isn't accidently pushed to production
# env.git_production_branch = 'production'


# The settings below here shouldn't need to be changed
env.user = USER
env.MACHINES = MACHINES

# Currently not used
# from project.settings.production import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
#env.DATABASE_NAME = DATABASE_NAME
#env.DATABASE_USER = DATABASE_USER
#env.DATABASE_PASSWORD = DATABASE_PASSWORD