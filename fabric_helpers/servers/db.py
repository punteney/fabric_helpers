import os

from fabric import state
from fabric.api import run
from fabric.contrib.files import exists, upload_template

from fabric_helpers.servers import Server

class PostgresqlServer(Server):
    def __init__(self, name="postgresql", 
            packages=['postgresql','postgresql-dev', 'postgresql-client', 'build-essental', 'libpq-dev'], 
            start_command='invoke-rc.d postgresql-8.4 start',
            restart_command='invoke-rc.d postgresql-8.4 restart',
            conf_files_path='/etc/postgresql/8.4/main/',
            conf_files=['pg_hba.conf', 'postgresql.conf'],
            listen_on=['internal',],
            port=5432,
            **kwargs):

        super(PostgresqlServer, self).__init__(name, packages=packages,
            start_command=start_command, 
            restart_command=restart_command, 
            conf_files_path=conf_files_path,
            conf_files=conf_files,
            listen_on=listen_on,
            port=port,
            **kwargs)
    
        
    
    def code_reload(self):
        pass

    def setup(self):
        self.upload_config()
        self.allow_access()
        self.restart()
        self.create_db()
        

    def config_template_context(self):
        return {
            'listen_addresses': ", ".join(self.get_listen_addresses()),
            'port': self.port,
        }

    def allow_access(self):
        hba_file = os.path.join(self.conf_files_path, 'hba.conf')
        for host in self.get_connection_addresses():
            append('host all all %s/32 trust' % host, hba_file, use_sudo=True)

    def create_db(self):
        db_user = getattr(state.env.django_settings, 'DATABASE_USER', state.env.user)
        db_name = getattr(state.env.django_settings, 'DATABASE_NAME', state.env.name)

        #run('sudo -u postgres createuser -S -d -R -l -i -W %s' % db_user)
        #run('sudo -u postgres createdb -O %s %s' % (db_user, db_name))
        print "****** Run the following commands to create the Postgres User and DB *******"
        print "****** Also configure the hba.conf file to match the permissions you want *******"
        print 'sudo -u postgres createuser -S -d -R -l -i -W %s' % db_user
        print 'sudo -u postgres createdb -O %s %s' % (db_user, db_name)
        print ""

