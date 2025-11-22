import logging
import os
import time

import docker
import pytest
from docker import DockerClient
from fastapi.testclient import TestClient
from pytest_docker.plugin import get_docker_ip
from sqlalchemy import create_engine, text

log = logging.getLogger(__name__)


def get_fast_api_client():
    import sys
    from pathlib import Path

    # Ensure the backend directory is in sys.path to prioritize project imports
    # From: backend/open_webui/test/util/abstract_integration_test.py
    # To:   backend/
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from open_webui.main import app

    with TestClient(app) as c:
        return c


class AbstractIntegrationTest:
    BASE_PATH = None

    def create_url(self, path="", query_params=None):
        if self.BASE_PATH is None:
            raise Exception("BASE_PATH is not set")
        parts = self.BASE_PATH.split("/")
        parts = [part.strip() for part in parts if part.strip() != ""]
        path_parts = path.split("/")
        path_parts = [part.strip() for part in path_parts if part.strip() != ""]

        # Build the path
        path_str = "/".join(parts + path_parts)
        if not path_str.startswith("/"):
            path_str = "/" + path_str

        query_parts = ""
        if query_params:
            query_parts = "&".join([f"{key}={value}" for key, value in query_params.items()])
            query_parts = f"?{query_parts}"
        return path_str + query_parts

    @classmethod
    def setup_class(cls):
        pass

    def setup_method(self):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def teardown_method(self):
        pass


class AbstractPostgresTest(AbstractIntegrationTest):
    DOCKER_CONTAINER_NAME = "postgres-test-container-will-get-deleted"
    docker_client: DockerClient

    @classmethod
    def _create_db_url(cls, env_vars_postgres: dict) -> str:
        host = get_docker_ip()
        user = env_vars_postgres["POSTGRES_USER"]
        pw = env_vars_postgres["POSTGRES_PASSWORD"]
        port = 8081
        db = env_vars_postgres["POSTGRES_DB"]
        return f"postgresql://{user}:{pw}@{host}:{port}/{db}"

    @classmethod
    def setup_class(cls):
        super().setup_class()
        try:
            env_vars_postgres = {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "example",
                "POSTGRES_DB": "openwebui",
            }
            cls.docker_client = docker.from_env()
            cls.docker_client.containers.run(
                "postgres:16.2",
                detach=True,
                environment=env_vars_postgres,
                name=cls.DOCKER_CONTAINER_NAME,
                ports={5432: ("0.0.0.0", 8081)},
                command="postgres -c log_statement=all",
            )
            time.sleep(0.5)

            database_url = cls._create_db_url(env_vars_postgres)
            os.environ["DATABASE_URL"] = database_url
            retries = 10
            db = None
            while retries > 0:
                try:
                    db = create_engine(database_url, pool_pre_ping=True)
                    db = db.connect()
                    log.info("postgres is ready!")
                    break
                except Exception as e:
                    log.warning(e)
                    time.sleep(3)
                    retries -= 1

            if db:
                # import must be after setting env!
                cls.fast_api_client = get_fast_api_client()
                db.close()
            else:
                raise Exception("Could not connect to Postgres")
        except Exception as ex:
            log.error(ex)
            cls.teardown_class()
            pytest.fail(f"Could not setup test environment: {ex}")

    def _check_db_connection(self):
        from open_webui.internal.db import Session

        retries = 10
        while retries > 0:
            try:
                Session.execute(text("SELECT 1"))
                Session.commit()
                break
            except Exception as e:
                Session.rollback()
                log.warning(e)
                time.sleep(3)
                retries -= 1

    def setup_method(self):
        super().setup_method()
        self._check_db_connection()

    @classmethod
    def teardown_class(cls) -> None:
        super().teardown_class()
        cls.docker_client.containers.get(cls.DOCKER_CONTAINER_NAME).remove(force=True)

    def teardown_method(self):
        from open_webui.internal.db import Session

        # rollback everything not yet committed
        Session.commit()

        # Clear all tables - use database-appropriate syntax
        tables = [
            "auth",
            "chat",
            "chatidtag",
            "document",
            "memory",
            "model",
            "prompt",
            "tag",
            "oauth_session",
            '"user"',
        ]

        # Check if we're using PostgreSQL or SQLite
        engine_name = Session.bind.dialect.name

        if engine_name == "postgresql":
            # PostgreSQL supports TRUNCATE with CASCADE
            for table in tables:
                Session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        else:
            # SQLite and others: use DELETE (slower but compatible)
            # Disable foreign key checks temporarily for SQLite
            if engine_name == "sqlite":
                Session.execute(text("PRAGMA foreign_keys = OFF"))

            for table in tables:
                Session.execute(text(f"DELETE FROM {table}"))

            if engine_name == "sqlite":
                Session.execute(text("PRAGMA foreign_keys = ON"))

        Session.commit()
