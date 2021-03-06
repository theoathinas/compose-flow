import logging

from .base import BaseSubcommand
from .kube_mixin import KubeMixIn
from .profile import Profile

ACTIONS = ['rancher', 'docker', 'rke', 'helm']
PROFILE_ACTIONS = ['docker', 'rancher']


class Deploy(BaseSubcommand, KubeMixIn):
    """
    Subcommand for deploying an image to the docker swarm
    """
    rw_env = True
    update_version_env_vars = True

    # apply all checks to deployment
    profile_checks = Profile.get_all_checks()

    @classmethod
    def fill_subparser(cls, parser, subparser):
        subparser.add_argument('action', nargs='?', default='docker', choices=ACTIONS)

    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    @property
    def setup_profile(self):
        if self.workflow.args.action in PROFILE_ACTIONS:
            return True
        else:
            return False

    def build_docker_command(self) -> str:
        return f"""docker stack deploy
            --prune
            --with-registry-auth
            --compose-file {self.workflow.profile.filename}
            {self.workflow.args.config_name}"""

    def build_rancher_command(self) -> list:
        self.switch_context()

        command = []

        for app in self.get_apps():
            # check if app is already installed - if so upgrade, if not install
            command.append(self.get_app_deploy_command(app))

        for manifest in self.get_manifests():
            if isinstance(manifest, str):
                manifest = {'path': manifest}
            command.append(self.get_manifest_deploy_command(manifest))

        return command

    def build_rke_command(self) -> str:
        return self.get_rke_deploy_command()

    def build_helm_command(self) -> str:
        command = []

        for app in self.get_helm_apps():
            command.append(self.get_app_deploy_command(app, target='helm'))
        return command

    def handle(self):
        args = self.workflow.args
        env = self.workflow.environment
        action = args.action

        try:
            action_method = getattr(self, 'build_' + action + '_command')
        except AttributeError:
            self.logger.error("Unknown deployment platform: %s", action)

        command = action_method()

        self.logger.info(command)

        if not args.dry_run:
            if isinstance(command, list):
                # If multiple commands are returned, run them one by one
                for c in command:
                    self.execute(c)
            else:
                self.execute(command)

            env.write()
