import asyncio

import httpx
import pytest

from src.app import app, activities


def make_request(method, path, **kwargs):
    async def _request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_request())


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = {
        name: {
            key: value.copy() if isinstance(value, list) else value
            for key, value in activity.items()
        }
        for name, activity in activities.items()
    }
    activities.clear()
    activities.update(original_activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    # No special setup needed for the root endpoint.

    # Act
    response = make_request("GET", "/")

    # Assert
    assert response.status_code == 307
    assert str(response.headers["location"]).endswith("/static/index.html")


def test_get_activities_returns_all_activities():
    # Arrange
    # The in-memory activities dataset is already available.

    # Act
    response = make_request("GET", "/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"


def test_signup_for_activity_adds_participant():
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = make_request("POST", "/activities/Chess Club/signup?email=" + email)

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in activities["Chess Club"]["participants"]


def test_signup_for_activity_rejects_duplicate_registration():
    # Arrange
    duplicate_email = "michael@mergington.edu"

    # Act
    response = make_request("POST", "/activities/Chess Club/signup?email=" + duplicate_email)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_for_missing_activity_returns_404():
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = make_request("POST", "/activities/Missing Club/signup?email=" + email)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_from_activity():
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = make_request("DELETE", "/activities/Chess Club/participants?email=" + email)

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_remove_participant_returns_404_for_missing_participant():
    # Arrange
    email = "not-a-member@mergington.edu"

    # Act
    response = make_request("DELETE", "/activities/Chess Club/participants?email=" + email)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"
