from flask.testing import FlaskClient


def test_home_page(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200
    assert b"flofriday" in response.data
    assert b"Used by 0 students" in response.data


# def test_verify_bad_url(client: FlaskClient):
#     response = client.get("/verify?url=nooAUrl")
#     assert response.status_code == 400


# def test_verify_not_tiss_url(client: FlaskClient):
#     response = client.get("/verify?url=https://example.com")
#     assert response.status_code == 400


# def test_verify(client: FlaskClient):
#     response = client.get(
#         "/verify?https://tiss.tuwien.ac.at/events/rest/calendar/personal?locale=en&token=justATestingTokenObviouslyNotReal"
#     )
#     assert response.status_code == 200
