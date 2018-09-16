import shlex

from unittest import TestCase, mock

from compose_flow import utils
from compose_flow.commands import Workflow


@mock.patch('compose_flow.commands.subcommands.env.os')
@mock.patch('compose_flow.commands.subcommands.remote.sh')
@mock.patch('compose_flow.commands.subcommands.passthrough_base.sh')
class PublishTestCase(TestCase):
    @mock.patch('compose_flow.commands.subcommands.env.utils')
    @mock.patch('compose_flow.commands.subcommands.env.docker')
    def test_profile_env(self, *mocks):
        """
        Ensure the VERSION is updated
        """
        docker_mock = mocks[0]
        docker_mock.get_config.return_value = "FOO=1\nBAR=2"

        utils_mock = mocks[1]
        utils_mock.get_tag_version.return_value = '0.0.1'
        utils_mock.render = utils.render

        command = shlex.split('-e dev publish')
        flow = Workflow(argv=command)

        flow.subcommand.build = mock.Mock()
        flow.subcommand.push = mock.Mock()

        flow.run()

        env_data = flow.environment.data

        self.assertEqual(True, 'VERSION' in env_data)

    @mock.patch('compose_flow.commands.subcommands.env.Env.rw_env', new=True)
    @mock.patch('compose_flow.commands.subcommands.env.utils')
    @mock.patch('compose_flow.commands.subcommands.env.docker')
    def test_update_version(self, *mocks):
        """
        Ensures that version in env is updated when the publish command is run
        """
        version = '1.2.3'
        new_version = '0.9.999'
        docker_image = 'foo:bar'

        docker_mock = mocks[0]
        docker_mock.get_config.return_value = f"FOO=1\nBAR=2\nVERSION={version}\nDOCKER_IMAGE={docker_image}"

        utils_mock = mocks[1]
        utils_mock.get_tag_version.return_value = new_version
        utils_mock.render = utils.render

        command = shlex.split('-e dev publish')
        flow = Workflow(argv=command)

        publish = flow.subcommand
        publish.get_built_docker_images = mock.Mock()
        publish.get_built_docker_images.return_value = []

        flow.run()

        env = flow.environment

        self.assertEqual(utils_mock.get_tag_version.return_value, env.data['VERSION'])
        self.assertEqual(f'foo:{new_version}', env.data['DOCKER_IMAGE'])
