from __future__ import with_statement
import os
import time

from fabric.api import hosts, run, sudo, cd
from fabric.state import env
from fabric.contrib.files import exists, append
from fabric.utils import warn
from fabric_helpers.servers import NginxServer, ApacheServer, Machines


################
# Environment SETUPS
###############
def dev():
    fab_config('dev')

def staging():
    fab_config('staging')

def production():
    fab_config('production')

def specific_server():
    env.hosts = ['slice9.geniusrocket.com',]

def fab_config(env_name):
    env.name = env_name
    env.hosts = machines.for_env(env.name)
    
class FabDeploy(object):
    @classmethod
    def set_project_paths(cls):
        # Setting the various project paths for reference throughout
        env.project_paths['virtual_env'] = os.path.join(env.project_paths['root'], env.git_branch)
        env.project_paths['releases'] = os.path.join(env.project_paths['root'], 'releases')
        env.project_paths['live'] = os.path.join(env.project_paths['root'], 'live')
        env.project_paths['repo'] = os.path.join(env.project_paths['root'], 'repository')
        env.project_paths['files'] = os.path.join('/var/', env.project_name)
        env.project_paths['upload'] = os.path.join(env.project_paths['files'], 'uploads')
        env.project_path = os.path.join(env.project_paths['live'], env.project_name) # Not created in the dict as it's symlinked not an actual dir

#######
# Install/Update functions
######

def install_from_scratch():
    full_os_install()
    project_install()
    set_global_config()
    set_sites_available()
    start_servers()

##### OS installation ######
def full_os_install():
    """
    Setup a fresh ubuntu server with needed packages.
    """
    sudo('locale-gen en_US.UTF-8')
    sudo('/usr/sbin/update-locale LANG=en_US.UTF-8')
    aptitude_update()
    install_base_packages()
    install_servers()
    install_graphic_packages()

def aptitude_update():
    sudo('aptitude -y update')
    sudo('aptitude -y safe-upgrade')
    sudo('aptitude -y full-upgrade')

def install_base_packages():
    sudo('aptitude -y install build-essential')
    sudo('aptitude -y install git-core subversion mercurial postgresql-client')
    sudo('aptitude -y install python-imaging python-setuptools ffmpegthumbnailer')
    sudo('aptitude -y install python-psycopg2 python-virtualenv python-dev')

def install_servers():
    for server in machines.get(env.host)['servers']:
        server.install()

def install_graphic_packages():
    sudo('aptitude -y install wv ghostscript libpng3 libjpeg62 texlive faad ffmpeg imagemagick')


#### Project creation ####
def project_install():
    create_project_paths()
    clone_repo()
    setup_project_virtualenv()
    project_update()

def create_project_paths():
    for path in env.project_paths.values():
        if not exists(path):
            sudo('mkdir -p %s;' % path)
    sudo('chown -R %s.%s %s' % (env.user, env.user, env.project_paths['root']))
    sudo('chown -R %s.%s %s' % (env.user, env.user, env.project_paths['files']))

def setup_project_virtualenv():
    create_virtualenv(env.project_paths['virtual_env'])
    run_env('easy_install --upgrade setuptools') # Bug in some older versions of setuptools
    run_env('easy_install pip')
    # pth_file = '%s/lib/python%s/site-packages/project.pth' % (env.project_paths['virtual_env'], str(machines.get(env.host)['python_version']))
    # pth_file = '%s/lib/python2.5/site-packages/project.pth' % (env.project_paths['virtual_env'])
    # 
    # append(env.project_path['live'], pth_file)
    # append(env.project_path, pth_file)
    # append(env.project_path+'/apps', pth_file)


def create_virtualenv(path, with_site_packages=True):
    if with_site_packages:
        run('virtualenv %s' % path)
    else:
        run('virtualenv --no-site-packages %s' % path)

def clone_repo():
    """Do initial clone of the git repo"""
    if exists(env.project_paths['repo']):
        # If it exists delete it to make sure we get the correct files/repo
        run('rm -rf %s' % env.project_paths['repo'])
    run('git clone %s %s' % (env.repo_path, env.project_paths['repo']))

#### Project updating ####
def project_update():
    """Updates the project to the latest version, installs all requirements and applies patches"""
    checkout_latest()
    install_project_requirements()
    symlink_release()
    django_syncdb()

def project_quick_update():
    """Updates the project to the latest version, installs all requirements and applies patches"""
    checkout_latest()
    symlink_release()

def checkout_latest():
    """Pull the latest code into the git repo and copy to a timestamped release directory"""
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    env.project_paths['release'] = os.path.join(env.project_paths['releases'], env.release)
    with cd(env.project_paths['repo']):
        if hasattr(env, 'git_branch'):
            git_branch = run('git branch')
            # If not on the selected branch we need to create it or switch to it
            if git_branch.find("* %s" % env.git_branch) == -1:
                if git_branch.find(' %s' % env.git_branch) == -1:
                    # Branch doesn't exist locally so check it out from the server and switch to it
                    run("git checkout --track -b %s origin/%s" % (env.git_branch, env.git_branch))
                else:
                    # Branch exists but isn't current so switch to it
                    run("git checkout %s" % env.git_branch)
        run("git pull")
    if not exists(env.project_paths['virtual_env']):
        # This is a new branch so create a new virtualenv for it
        setup_project_virtualenv()
    run('cp -R %s %s; rm -rf %s/.git*' 
        % (env.project_paths['repo'], env.project_paths['release'], env.project_paths['release']))

def install_project_requirements():
   """Install the required packages using pip"""
   run_env('pip install -r %s/deploy/requirements_pip.txt -E %s' % (env.project_paths['release'], env.project_paths['virtual_env']))

def symlink_release(release=None):
    """Symlink our current release, uploads and settings file"""
    if not release:
        # Setting environment variables to current release
        release = set_latest_release()
    
    # Linking the main project
    project_dir = env.project_path
    if exists(project_dir):
        run('rm %s' % project_dir)
    run('ln -s %s %s' % (env.project_paths['release'], project_dir))
    
    # Linking the settings file
    settings_file = '%s/settings.py' % env.project_paths['live']
    if exists(settings_file):
        run('rm %s' % settings_file)
    run('ln -s %s/gr_select/settings/%s.py %s' % (env.project_paths['release'], env.name, settings_file))

    # Linking the active virtual_env file
    virtual_env_dir = os.path.join(env.project_paths['live'], 'virtual_env')
    if exists(virtual_env_dir):
        run('rm %s' % virtual_env_dir)
    run('ln -s %s %s' % (env.project_paths['virtual_env'], virtual_env_dir))
    
    # Linking site-packages dir
    packages_dir = '%s/site-packages' % env.project_paths['live']
    if exists(packages_dir):
        run('rm %s' % packages_dir)
    run('ln -s %s/lib/python%s/site-packages %s' % (env.project_paths['virtual_env'], machines.get(env.host)['python_version'], packages_dir))

    if APACHE in machines.get(env.host)['servers']:
        # Linking the wsgi dir
        wsgi_dir = APACHE.wsgi_dir()
        if exists(wsgi_dir):
            run('rm %s' % wsgi_dir)
        run('ln -s %s/config/wsgi/%s %s' % (env.project_paths['release'], env.name, wsgi_dir))

    #if NGINX in machines.get(env.host)['servers']:
        # Linking upload dir
        # upload_dir = os.path.join(env.project_paths['live'], 'gr/media/uploads')
        #        if exists(upload_dir):
        #            run('rm %s' % upload_dir)
        #        run('ln -s /var/gr_select/uploads/ %s' % (upload_dir))
        #        # Linking upload dir outside of newdesign (moving everything to here overtime)
        #        upload_dir = os.path.join(env.project_paths['live'], 'gr/media/uploads')
        #        if exists(upload_dir):
        #            run('rm %s' % upload_dir)
        #        run('ln -s /var/gr_select/uploads/ %s' % (upload_dir))


        # Linking temp dir
        # dir = os.path.join(env.project_paths['live'], 'gr/media/temp')
        #         if exists(dir):
        #             run('rm %s' % dir)
        #         run('ln -s /var/gr/temp/ %s' % (dir))
        #         dir = os.path.join(env.project_paths['live'], 'gr/media/temp')
        #         if exists(dir):
        #             run('rm %s' % dir)
        #         run('ln -s /var/gr/temp/ %s' % (dir))


def db_migrate():
    run_env('cd %s; django-admin.py migrate --settings=settings' % env.project_paths['live'])

def django_syncdb():
    run_env('cd %s; django-admin.py syncdb --settings=settings --noinput' % env.project_paths['live'])
    db_migrate()

def sync_db_from_prod():
    """Sync the product database to another server"""
    # TODO WHEN PROD IS UPDATED TO NEW SETTINGS
    print env.name
    production()
    print env.name
    staging()
    print env.name
    
    warn('**** If you want this to run without prompting for a password you must create a ~/.pgpass file on the server this command is run from')
    # TODO ONCE PROD IS UPDATED TO NEW STYLE
    # This will be for the new setup not the current live set
    # run('cd %s; source bin/activate; cd live; django-admin.py backupdb' )


### Serverwide configs/actions ####
def set_global_config():
    """These are one time global configs for setting up things like the nginx.conf and apache.conf files"""
    timestamp = time.strftime('%Y%m%d%H%M%S')
    # Setting server config files
    for server in machines.get(env.host)['servers']:
        server.setup_config()

def set_sites_available():
    """Sets the nginx and apache sites enabled"""
    for server in machines.get(env.host)['servers']:
        if hasattr(server, 'sites'):
            server.enable_sites()
            server.deactivate_default()

def start_servers():
    for server in machines.get(env.host)['servers']:
        server.start()

def restart_servers():
    for server in machines.get(env.host)['servers']:
        server.restart()

def reload_servers():
    for server in machines.get(env.host)['servers']:
        server.quick_reload()

def update_files():
    checkout_latest()
    install_project_requirements()
    symlink_release()


#### Release Management ####
def get_releases():
    listing = run('ls %s' % (env.project_paths['releases']))
    release_list = listing.split('\n')
    releases = []
    for r in release_list:
        if r != '':
            releases.append(int(r.strip()))
    releases.sort()
    return releases
    
def set_latest_release():
    releases = get_releases()
    return set_release(releases[-1])

def set_previous_release():
    # This sets the release to previous release... for reverting
    releases = get_releases()
    if len(releases) > 1:
        return set_release(releases[-2])
    return None #TODO Make this an exception

def set_release(release):
    env.release = str(release)
    env.project_paths['release'] = os.path.join(env.project_paths['releases'], env.release)
    return env.release

def delete_release(release):
    del_path = os.path.join(env.project_paths['releases'], release)
    if exists(del_path):
        run('rm -rf %s' % del_path)


### Helpful functions ####
def rollback():
    # This will rollback to the previous release
    # Any system changes will still be in effect though
    # installed packages, db changes, global configs, etc.
    symlink_release(release=set_previous_release())

def push():
    project_update()
    restart_servers()
    
def push_quick():
    project_quick_update()
    reload_servers()

def delete_old_releases():
    releases = get_releases()
    # Leave the last 10 releases
    if len(releases) > 10:
        for release in releases[:-10]:
            delete_release(str(release))

def show_maintenance():
    NGINX.enable_site('maintenance')
    NGINX.restart()

def remove_maintenance():
    NGINX.disable_site('maintenance')
    NGINX.restart()

def change_owner(path, user='gr', group='fabric', recursive=True):
    if recursive:
        sudo('chown -R %s:%s %s' % (user, group, path))
    else:
        sudo('chown %s:%s %s' % (user, group, path))

# Runs the command within the virtualenv
def run_env(cmd, *a, **kw):
    run("cd %s; source bin/activate; %s" % (env.project_paths['virtual_env'], cmd), *a, **kw)


