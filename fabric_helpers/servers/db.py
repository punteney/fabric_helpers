import os

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
#         settings = __import__("settings.%s" % env.name)
# 
# from project.settings.production import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
# env.DATABASE_NAME = DATABASE_NAME
# env.DATABASE_USER = DATABASE_USER
# env.DATABASE_PASSWORD = DATABASE_PASSWORD

        run('sudo -u postgres createuser -S -d -R -l -i -W %s' % state.env.DATABASE_USER)
        run('sudo -u postgres createdb -O %s %s' % (state.env.DATABASE_USER, state.env.DATABASE_NAME))

