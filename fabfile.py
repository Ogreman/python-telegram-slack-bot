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
    with settings(warn_only=True):
        local("git add -u && git commit -m '%s'" % words)


def push(branch="master"):
    with settings(warn_only=True):
        local("git push %s %s" % (env.hosts[0], branch))


def prepare(branch="_dummy", stash=True):
    with cd(env.REMOTE_PROJECT_PATH):
        if stash:
            run("git stash")
        with settings(warn_only=True):
            result = run("git checkout -b %s" % branch)
        if result.failed:
            run("git checkout %s" % branch)


def finalise(branch="master", stash=True):
    with cd(env.REMOTE_PROJECT_PATH):
        run("git checkout %s" % branch)
        if stash:
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


def rmdirs(prompt=True):
    if not prompt:
        run("rm -rf %s" % env.REMOTE_PROJECT_PATH)
        return
    if confirm("Delete everything?"):
        run("rm -rf %s" % env.REMOTE_PROJECT_PATH)


def initgit():
    with cd(env.REMOTE_PROJECT_PATH):
        run("git init")


def scppa():
    local("scp %s raffers:/home/james/projects/t2s/" % postactivate)


def installdeps():
    with settings(warn_only=True):
        with cd(env.REMOTE_PROJECT_PATH):
            run("pip install -r requirements.txt")


def new():
    kill()
    mkdir()
    initgit()
    prepare(stash=False)
    push()
    finalise(stash=False)
    clean()
    scppa()
    installdeps()
    start()


def refresh():
    kill()
    rmdirs(prompt=False)
    new()


def deploy(m):
    commit(m)
    kill()
    prepare()
    push()
    finalise()
    clean()
    start()
