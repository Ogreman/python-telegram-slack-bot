import os
from fabric.api import local, settings, run, env, cd

env.use_ssh_config = True
env.hosts = ['raffers']
postactivate = os.environ['VIRTUAL_ENV'] + '/bin/postactivate'


with open(postactivate, 'r') as pa:
    for line in pa:
        try:
            key, val = line.split('=')
            key = key.split(' ')[1]
            env[key] = val.replace('"', '').strip()
        except (IndexError, ValueError):
            pass


def mkdirs():
    run("mkdir -p %s" % env.REMOTE_PROJECT_PATH)


def start():
    with settings(warn_only=True):
        with cd(env.REMOTE_PROJECT_PATH):
            run('source postactivate && dtach -n `mktemp -u /tmp/dtach.XXXX` python %s/t2sbot.py' % env.REMOTE_PROJECT_PATH)


def commit(words):
    local("git add -u && git commit -m '%s'" % words)


def push(branch="master"):
    local("git push %s %s" % (env.hosts[0], branch))


def prepare(branch="_dummy"):
    with cd(env.REMOTE_PROJECT_PATH):
        run("git stash")
        with settings(warn_only=True):
            result = run("git checkout -b %s" % branch)
        if result.failed:
            run("git checkout %s" % branch)


def finalise(branch="master"):
    with cd(env.REMOTE_PROJECT_PATH):
        run("git checkout %s" % branch)
        run("git stash pop")


def clean(branch="_dummy"):
    with cd(env.REMOTE_PROJECT_PATH):
        with settings(warn_only=True):
            run("git branch -D %s" % branch)


def kill():
    pid = run("ps aux | grep t2s | grep -v grep | awk '{print $2}'")
    for p in pid.split('\n'):
        if p:
            run("kill %d" % int(p))


def running():
    run("ps aux | grep t2s | grep -v grep | awk '{print $2}'")


def deploy(m):
    commit(m)
    kill()
    prepare()
    push()
    finalise()
    clean()
    start()
