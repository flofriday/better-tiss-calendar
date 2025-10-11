from typing import Any

import pytest
from flask.testing import FlaskClient, FlaskCliRunner
from syrupy.extensions.single_file import SingleFileSnapshotExtension

from app import app as backendapp


@pytest.fixture()
def app():
    app = backendapp
    app.config.update(
        {
            "TESTING": True,
        }
    )

    yield app


@pytest.fixture()
def client(app) -> FlaskClient:
    return app.test_client()


@pytest.fixture()
def runner(app) -> FlaskCliRunner:
    return app.test_cli_runner()


class ICALSnapshotExtension(SingleFileSnapshotExtension):
    file_extension = "ical"

    def serialize(self, data: str, **kwargs: Any) -> bytes:
        return data.encode("utf-8")


@pytest.fixture
def snapshot_ical(snapshot):
    return snapshot.use_extension(ICALSnapshotExtension)
