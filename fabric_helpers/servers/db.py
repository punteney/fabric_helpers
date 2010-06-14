from fabric_helpers.servers import Server

class PostgresqlServer(Server):
    def __init__(self, name="postgresql", 
            packages=['postgresql','postgresql-dev'], 
            start_command='invoke-rc.d postgresql-8.4 start',
            restart_command='invoke-rc.d postgresql-8.4 restart',
            conf_files_path='/etc/postgresql/8.4/main/',
            conf_files=['pg_hba.conf', 'postgresql.conf'],
            **kwargs):

        super(PostgresqlServer, self).__init__(name, packages=packages,
            start_command=start_command, 
            restart_command=restart_command, 
            conf_files_path=conf_files_path,
            conf_files=conf_files,
            **kwargs)
    
    def code_reload(self):
        pass

#    def setup(self):
#        self.setup_config()
        # self.create_db()
    
    # def create_db(self):
    #   Currently requires user input, need to determine how to create these without needing user input
    #     run('sudo -u postgres createuser %s' % state.env.DATABASE_USER)
    #     run('sudo -u postgres createdb -O %s %s' % (state.env.DATABASE_USER, state.env.DATABASE_NAME))
