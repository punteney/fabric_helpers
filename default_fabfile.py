from fabric_helpers import *
from fabric_helpers.servers import Machines, Machine, PostgresqlServer, NginxServer, ApacheServer

# A "Machine" is a representation of an actual system the 'physical server'
# A "Server" is a representation of a specific server software to be installed
#   on the Machine. Things like Postgres, Apache, etc.


# The user on the machine, this should be a generic user (ie not a real 
# individual) or a user that is specific to this project.
USER = 'PROJECT_USER'

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
    Machine('SERVER IP OR HOSTNAME HERE', ENVIRONMENTS['production'], 
        short_name="prod", servers=[POSTGRES, APACHE, NGINX]),

#   Uncomment the following lines for a matching staging server
#    Machine('SERVER IP OR HOSTNAME HERE', ENVIRONMENTS['staging'], 
#        short_name="prod", servers=[POSTGRES, APACHE, NGINX]),
])

# This will be the folder that all of the project files are kept in.
env.project_name = 'PROJECT NAME'

# The path to your git repo ie:
# env.git_repo = 'git://github.com/punteney/fab_helpers.git'
env.git_repo = 'THE PATH TO YOU GIT REPO'

# The name and location of your project folder. By default it's set to:
# /home/USERNAME/PROJECTNAME 
env.project_root = os.path.join('/home/', USER, env.project_name)

# The name of the actual project folder within the project_root defined above
env.project_folder_name = 'project'

# The settings below here shouldn't need to be changed
env.user = USER
env.MACHINES = MACHINES

# Currently not used
# from project.settings.production import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
#env.DATABASE_NAME = DATABASE_NAME
#env.DATABASE_USER = DATABASE_USER
#env.DATABASE_PASSWORD = DATABASE_PASSWORD