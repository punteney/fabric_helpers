from fabric_helpers import *
from fabric_helpers.servers import Machines, Machine, PostgresqlServer, NginxServer, ApacheServer
# from project.settings.production import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD

# The holder for the various machines that this fabfile is concerned with
MACHINES = Machines()

# The user on the server, this should be a user generic user (ie not a real 
# individual) or a user that is specific to this project.
USER = 'PROJECT_USER'

# The default Postgres sever configuration
POSTGRES = PostgresqlServer()

# The default Apache server configuration
APACHE = ApacheServer(sites=['django_site'])
NGINX = NginxServer(sites=['django_site'])

# Registering individual machines
MACHINES.register(
    Machine('173.203.83.187', ENVIRONMENTS['production'], 
        short_name="prod", servers=[POSTGRES, APACHE, NGINX])
)

env.MACHINES = MACHINES
env.user = USER
env.project_name = 'zoo'
env.project_folder_name = 'project' 
env.project_root = os.path.join('/home/', USER, env.project_name)
env.git_repo = 'git://github.com/punteney/fab_test.git'

# Currently not used
#env.DATABASE_NAME = DATABASE_NAME
#env.DATABASE_USER = DATABASE_USER
#env.DATABASE_PASSWORD = DATABASE_PASSWORD