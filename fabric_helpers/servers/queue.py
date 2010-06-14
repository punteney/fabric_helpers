import os

from fabric import state
from fabric.api import run, sudo, cd, local

from fabric_helpers.servers import Server


class RabbitServer(Server):
    def __init__(self, name='rabbit', packages=['rabbitmq-server'],
            start_command='/etc/init.d/rabbitmq-server start',
            restart_command='/etc/init.d/rabbitmq-server restart',
            **kwargs):
        kwargs['packages'] = packages
        kwargs['start_command'] = start_command
        kwargs['restart_command'] = restart_command
        super(RabbitServer, self).__init__(name, **kwargs)

    def setup_config(self):
        sudo("rabbitmqctl add_user %s rabbitpass" % state.env.user)
        sudo("rabbitmqctl add_vhost %s" % state.env.project_name)
        sudo('rabbitmqctl map_user_vhost %s gr_select' % state.env.user)
    
    def code_reload(self):
        pass


class CeleryServer(Server):
    def __init__(self, name='celery', 
            packages=['rabbitmq-server'],
            pip_packages=['celery==1.0.5'],
            start_command='/etc/init.d/celeryd start', 
            restart_command='/etc/init.d/celeryd restart', 
            **kwargs):
        
        kwargs['packages'] = packages
        kwargs['pip_packages'] = pip_packages
        kwargs['start_command'] = start_command
        kwargs['restart_command'] = restart_command
        
        super(CeleryServer, self).__init__(name, **kwargs)

    def setup_config(self):
        run('mkdir %s' % os.path.join(state.env.paths['root'], 'celery'))
        sudo('ln %s /etc/init.d/celeryd') % (os.path.join(state.env.paths['live'], 'config/init_scripts/celeryd'))
        sudo('chmod +x /etc/init.d/celeryd')
        sudo('update-rc.d celeryd defaults')

