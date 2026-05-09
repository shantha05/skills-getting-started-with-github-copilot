"""
Tests for the Mergington High School Activities API
Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Activities endpoint should return 200 status"""
        # Arrange
        endpoint = "/activities"

        # Act
        response = client.get(endpoint)

        # Assert
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Activities endpoint should return a dictionary"""
        # Arrange
        endpoint = "/activities"

        # Act
        response = client.get(endpoint)
        data = response.json()

        # Assert
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_has_expected_fields(self, client):
        """Each activity should have required fields"""
        # Arrange
        endpoint = "/activities"
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get(endpoint)
        activities = response.json()
        first_activity = list(activities.values())[0]

        # Assert
        assert required_fields.issubset(first_activity.keys())

    def test_get_activities_participants_are_lists(self, client):
        """Each activity's participants should be a list of strings"""
        # Arrange
        endpoint = "/activities"

        # Act
        response = client.get(endpoint)
        activities = response.json()

        # Assert
        for activity_name, activity in activities.items():
            assert isinstance(activity["participants"], list), \
                f"Participants for {activity_name} should be a list"
            for participant in activity["participants"]:
                assert isinstance(participant, str), \
                    f"Participant {participant} should be a string"


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """New participant can successfully sign up for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        endpoint = f"/activities/{activity_name}/signup"

        # Act
        response = client.post(endpoint, params={"email": email})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """After signup, participant should appear in activity list"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent2@mergington.edu"
        endpoint = f"/activities/{activity_name}/signup"

        # Act
        client.post(endpoint, params={"email": email})
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_participant_fails(self, client):
        """Signing up a participant twice should return 400 error"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        endpoint = f"/activities/{activity_name}/signup"

        # Act
        response = client.post(endpoint, params={"email": email})

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Signup to non-existent activity should return 404"""
        # Arrange
        activity_name = "NonExistent Activity"
        email = "test@mergington.edu"
        endpoint = f"/activities/{activity_name}/signup"

        # Act
        response = client.post(endpoint, params={"email": email})

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_increments_participant_count(self, client):
        """Signup should increase participant count by exactly 1"""
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent3@mergington.edu"
        endpoint = f"/activities/{activity_name}/signup"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])

        # Act
        client.post(endpoint, params={"email": email})
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])

        # Assert
        assert count_after == count_before + 1


class TestUnregisterParticipant:
    """Test suite for DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """Participant can successfully unregister from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Pre-registered
        endpoint = f"/activities/{activity_name}/participants"

        # Act
        response = client.delete(endpoint, params={"email": email})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant_from_activity(self, client):
        """After unregister, participant should no longer appear in activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "daniel@mergington.edu"  # Pre-registered
        endpoint = f"/activities/{activity_name}/participants"

        # Act
        client.delete(endpoint, params={"email": email})
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert email not in activities[activity_name]["participants"]

    def test_unregister_not_registered_participant_fails(self, client):
        """Unregistering a non-registered participant should return 404"""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        endpoint = f"/activities/{activity_name}/participants"

        # Act
        response = client.delete(endpoint, params={"email": email})

        # Assert
        assert response.status_code == 404
        assert "not signed up for this activity" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Unregistering from non-existent activity should return 404"""
        # Arrange
        activity_name = "NonExistent Activity"
        email = "test@mergington.edu"
        endpoint = f"/activities/{activity_name}/participants"

        # Act
        response = client.delete(endpoint, params={"email": email})

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_decrements_participant_count(self, client):
        """Unregister should decrease participant count by exactly 1"""
        # Arrange
        activity_name = "Drama Club"
        email = "lucas@mergington.edu"  # Pre-registered
        endpoint = f"/activities/{activity_name}/participants"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])

        # Act
        client.delete(endpoint, params={"email": email})
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])

        # Assert
        assert count_after == count_before - 1


class TestRootRedirect:
    """Test suite for GET / endpoint"""

    def test_root_path_redirects_to_index(self, client):
        """Root path should redirect to static index.html"""
        # Arrange
        endpoint = "/"

        # Act
        response = client.get(endpoint, follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
