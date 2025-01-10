"""
Docker Installer
"""
import copy
import subprocess

import utils.color_print as color_print
import utils.verbose as verbose_func
import config
from core.env_managers.installer import Installer


class DockerInstaller(Installer):
    # _docker_gadgets is only for uninstall process
    _docker_gadgets = [
        'docker-ce',
        'docker-ce-cli',
        'docker',
        'docker-engine',
        'docker.io',
        'containerd.io',
        'runc',
    ]
    _docker_requirements = [
        'apt-transport-https',
        'ca-certificates',
        'gnupg-agent',
        'software-properties-common',
    ]

    @classmethod
    def uninstall(cls, verbose=False):
        """Uninstall Docker.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        for gadget in cls._docker_gadgets:
            temp_cmd = copy.copy(cls.cmd_apt_uninstall)
            temp_cmd.append(gadget)
            subprocess.run(
                temp_cmd,
                stdout=stdout,
                stderr=stderr,
                check=False
            )
            
    #uninstall_containerd_only
    @classmethod
    def uninstall_containerd_only(cls, verbose=False):
        """Uninstall containerd only.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = copy.copy(cls.cmd_apt_uninstall)
        temp_cmd.append('containerd.io')
        subprocess.run(
            temp_cmd,
            stdout=stdout,
            stderr=stderr,
            check=False
        )        # uninstall containerd only

    #DockerInstaller.uninstall_runc(verbose=args.verbose)
    @classmethod
    def uninstall_runc(cls, verbose=False):
        """Uninstall runc.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('uninstalling runc')
        # currently we just remove the runc binary
        runc_commands = [
                'rm /usr/bin/runc',
                'systemctl daemon-reload',
                'systemctl restart docker'            # 重启 docker 服务
            ]
        for command in runc_commands:
            subprocess.run(
                command,
                stdout=stdout,
                stderr=stderr,
                check=True
            )
        

    @classmethod
    def install_by_version(cls, gadgets, context=None, verbose=False):
        """Install Docker with specified version.

        Args:
            gadgets: Docker gadgets (e.g. docker-ce).
            context: Currently not used.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether Docker is successfully installed or not.
        """
        if not cls._pre_install(verbose=verbose):
            color_print.error('failed to install prerequisites')
            return False
        for gadget in gadgets:
            if not cls._install_one_gadget_by_version(
                    gadget['name'], gadget['version'], verbose=verbose):
                color_print.error(
                    'some errors happened during docker installation')
                return True
        return True

    @classmethod
    def _pre_install(cls, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        # install requirements
        color_print.debug('installing prerequisites')
        try:
            if not cls._apt_update(verbose=verbose):
                return False
            subprocess.run(
                cls.cmd_apt_install +
                cls._docker_requirements,
                stdout=stdout,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            return False
        cls._add_apt_repository(gpg_url=config.docker_apt_repo_gpg,
                                repo_entry=config.docker_apt_repo_entry, verbose=verbose)
        for repo in config.containerd_apt_repo_entries:
            cls._add_apt_repository(repo_entry=repo, verbose=verbose)

        cls._apt_update(verbose=verbose)

        return True

    #DockerInstaller.install_runc(install_version, verbose=args.verbose)
    @classmethod
    def install_runc(cls, install_version, verbose=False):
        """Install runc.

        Args:
            install_version: Version of runc.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether runc is successfully installed or not.
        commands needed:
        runc_commands=[]
        url='https://github.com/opencontainers/runc/releases/download/v'+install_version+'/runc.amd64'
        runc_commands.append('sudo mv /usr/bin/runc /usr/bin/runc.bak')
        runc_commands.append('curl -L -o /usr/bin/runc  '+url)
        runc_commands.append('chmod +x /usr/bin/runc')
        runc_commands.append('systemctl daemon-reload')
        runc_commands.append('systemctl restart docker')
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('installing runc with version {version}'.format(
            version=install_version))
        try:
            # 构造下载 URL
            url = f'https://github.com/opencontainers/runc/releases/download/v{install_version}/runc.amd64'
            # 构建更新命令
            runc_commands = [
                'sudo mv /usr/bin/runc /usr/bin/runc.bak',  # 备份当前的 runc
                f'curl -L -o /usr/bin/runc {url}',          # 下载指定版本的 runc
                'chmod +x /usr/bin/runc',                   # 添加执行权限
                'systemctl daemon-reload',                  # 重载 systemd 守护进程
                'systemctl restart docker'                  # 重启 docker 服务
            ]
            for command in runc_commands:
                subprocess.run(
                    command,
                    stdout=stdout,
                    stderr=stderr,
                    check=True
                )
        except subprocess.CalledProcessError:
            return False
        return True

if __name__ == "__main__":
    DockerInstaller.uninstall()
    import sys
    if len(sys.argv) > 1:
        test_version = sys.argv[1]
    else:
        test_version = '17.03.0'
    temp_gadgets = [{'name': 'docker-ce', 'version': test_version}]
    DockerInstaller.install_by_version(temp_gadgets)
