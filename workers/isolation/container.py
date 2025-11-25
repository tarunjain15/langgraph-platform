"""
Container Isolation (R13.3)

Docker-based journey isolation for workers.
Each user journey gets a dedicated container with isolated filesystem.

Sacred Constraint: JOURNEY_ISOLATION
- One container per user_journey_id
- Isolated network namespace
- Bind-mounted workspace volume
- Read-only root filesystem (security)
"""

import asyncio
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ContainerIsolation:
    """
    Docker-based journey isolation.

    Provides:
    - Isolated container per user journey
    - Bind-mounted workspace (persistent state)
    - Network isolation
    - Read-only root filesystem
    """

    # Docker client (lazy initialization to avoid import errors in tests)
    _client = None

    @classmethod
    def _get_client(cls):
        """Get Docker client (lazy init)"""
        if cls._client is None:
            try:
                import docker
                cls._client = docker.from_env()
            except ImportError:
                raise ImportError(
                    "Docker SDK not installed. Install with: pip install docker"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to connect to Docker: {e}")
        return cls._client

    @staticmethod
    async def spawn_container(
        user_journey_id: str,
        workspace_path: str,
        container_image: str = "python:3.11-slim",
        read_only: bool = True
    ) -> str:
        """
        Spawn isolated docker container for user journey.

        Args:
            user_journey_id: Journey identifier
            workspace_path: Host workspace path
            container_image: Docker image to use
            read_only: Make root filesystem read-only (security)

        Returns:
            Container ID

        Creates:
            - Isolated network namespace
            - Bind-mounted workspace volume (rw)
            - Read-only root filesystem (optional)
            - Environment variable: USER_JOURNEY_ID

        Raises:
            RuntimeError: If container spawn fails
        """
        client = ContainerIsolation._get_client()

        # Create workspace directory on host
        Path(workspace_path).mkdir(parents=True, exist_ok=True)

        try:
            # Spawn container in detached mode
            container = await asyncio.to_thread(
                client.containers.run,
                image=container_image,
                name=f"worker_{user_journey_id}",
                detach=True,
                network_mode="bridge",  # Isolated network
                volumes={
                    workspace_path: {
                        "bind": "/workspace",
                        "mode": "rw"
                    }
                },
                read_only=read_only,  # Root filesystem read-only
                tmpfs={"/tmp": "rw,size=100m"},  # Writable tmp
                environment={
                    "USER_JOURNEY_ID": user_journey_id
                },
                labels={
                    "langgraph.user_journey_id": user_journey_id,
                    "langgraph.isolation": "container"
                },
                command="tail -f /dev/null",  # Keep container alive
                remove=False  # Don't auto-remove (we need to inspect)
            )

            logger.info(
                f"Spawned container {container.id[:12]} for journey {user_journey_id}"
            )

            return container.id

        except Exception as e:
            raise RuntimeError(
                f"Failed to spawn container for journey {user_journey_id}: {e}"
            )

    @staticmethod
    async def kill_container(container_id: str):
        """
        Kill and remove container.

        Args:
            container_id: Container ID to kill

        Flow:
            1. Get container by ID
            2. Kill container (SIGKILL)
            3. Remove container
        """
        client = ContainerIsolation._get_client()

        try:
            container = await asyncio.to_thread(
                client.containers.get,
                container_id
            )
            await asyncio.to_thread(container.kill)
            await asyncio.to_thread(container.remove)

            logger.info(f"Killed container {container_id[:12]}")

        except Exception as e:
            # Ignore errors if container already removed
            logger.debug(f"Container {container_id[:12]} cleanup: {e}")
            pass

    @staticmethod
    async def exec_in_container(
        container_id: str,
        command: str,
        timeout: int = 30,
        workdir: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Execute command in container.

        Args:
            container_id: Container ID
            command: Command to execute (string or list)
            timeout: Timeout in seconds
            workdir: Working directory for command

        Returns:
            {
                "exit_code": int,
                "output": str
            }

        Raises:
            RuntimeError: If command execution fails
        """
        client = ContainerIsolation._get_client()

        try:
            container = await asyncio.to_thread(
                client.containers.get,
                container_id
            )

            # Execute command with timeout
            exec_result = await asyncio.wait_for(
                asyncio.to_thread(
                    container.exec_run,
                    cmd=command,
                    demux=False,
                    workdir=workdir
                ),
                timeout=timeout
            )

            # Decode output
            output = ""
            if exec_result.output:
                if isinstance(exec_result.output, bytes):
                    output = exec_result.output.decode('utf-8', errors='replace')
                else:
                    output = str(exec_result.output)

            return {
                "exit_code": exec_result.exit_code,
                "output": output
            }

        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Command timed out after {timeout}s: {command}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to execute command in container {container_id[:12]}: {e}"
            )

    @staticmethod
    async def get_container_status(container_id: str) -> Dict[str, any]:
        """
        Get container status.

        Args:
            container_id: Container ID

        Returns:
            {
                "status": str,  # running, exited, etc.
                "created": str,
                "started": str
            }
        """
        client = ContainerIsolation._get_client()

        try:
            container = await asyncio.to_thread(
                client.containers.get,
                container_id
            )

            status = container.status
            created = container.attrs.get('Created', '')
            started = container.attrs['State'].get('StartedAt', '')

            return {
                "status": status,
                "created": created,
                "started": started
            }

        except Exception as e:
            raise RuntimeError(
                f"Failed to get container status for {container_id[:12]}: {e}"
            )

    @staticmethod
    async def copy_to_container(
        container_id: str,
        local_path: str,
        container_path: str
    ):
        """
        Copy file/directory to container.

        Args:
            container_id: Container ID
            local_path: Local file/directory path
            container_path: Destination path in container
        """
        client = ContainerIsolation._get_client()

        try:
            container = await asyncio.to_thread(
                client.containers.get,
                container_id
            )

            # Read local file as tar
            import tarfile
            import io

            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar.add(local_path, arcname=Path(local_path).name)

            tar_stream.seek(0)

            # Copy to container
            await asyncio.to_thread(
                container.put_archive,
                path=container_path,
                data=tar_stream
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to copy to container {container_id[:12]}: {e}"
            )
