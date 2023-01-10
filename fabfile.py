from fabric.api import env, run, cd, task
import os

env.use_ssh_config = False


@task
def sit():
    env.project_dahsboard_home = "/home/webapps/apps/stepwise-platform/dashboard"
    env.project_api_home = "/home/webapps/apps/stepwise-platform/api"
    env.hosts = [os.environ.get("SERVER_HOST")]
    env.user = os.environ.get("SERVER_USER")
    env.password = os.environ.get("SERVER_PASSWORD")
    env.branch_name = "origin dev"
    env.docker_compose = "docker-compose-sit.yml"

@task
def stage():
    env.project_dahsboard_home = "/home/webapps/apps/stepwise-stage/dashboard"
    env.project_api_home = "/home/webapps/apps/stepwise-stage/api"
    env.hosts = [os.environ.get("SERVER_HOST")]
    env.user = os.environ.get("SERVER_USER")
    env.password = os.environ.get("SERVER_PASSWORD")
    env.branch_name = "origin stage"
    env.docker_compose = "docker-compose-stage.yml"


@task
def update():
    with cd(env.project_api_home):
        run(f"git pull {env.branch_name}")
        run(f"docker-compose -f {env.docker_compose} build")
        run(f"docker-compose -f {env.docker_compose} stop")
        run(f"docker-compose -f {env.docker_compose} up -d")
        run(f"docker-compose -f {env.docker_compose} start")

    with cd(env.project_dahsboard_home):
        run(f"git pull {env.branch_name}")
        run("yarn install")
        run("yarn build")
