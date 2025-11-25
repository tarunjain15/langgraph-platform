"""
Worker Isolation Module (R13.3)

Provides isolation mechanisms for worker instances:
- Container isolation (Docker-based)
- Process isolation (future)
- Thread isolation (future)
"""

from workers.isolation.container import ContainerIsolation

__all__ = ["ContainerIsolation"]
