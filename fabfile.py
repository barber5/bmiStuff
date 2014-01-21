import sys
import time
import fabric.exceptions
from fabric.api import *
from fabric.context_managers import cd
from fabric.contrib.files import append

env.hosts = ['barber5@ncbolabs-dev4.stanford.edu']

@task
def deploy(message="no message", name="ricktest"):                  
    local('git add .')
    with settings(warn_only=True): 
        local('git commit -m "%s"' % message)
    local('git pull origin master && git push origin master')        

    with cd('bmiStuff'):                
        run('git fetch')
        run('git reset --hard origin/master')
        
