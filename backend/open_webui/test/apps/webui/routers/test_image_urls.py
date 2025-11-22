"""
Test image URL compatibility for user and model profile images.
Tests that various URL formats (http, https, relative) are properly redirected.
"""
from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user
from fastapi import status


class TestImageURLCompatibility(AbstractPostgresTest):
    """Test that image URLs work correctly with various formats"""
    
    BASE_PATH = "/api/v1/users"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.users import Users
        from open_webui.models.models import Models

        cls.users = Users
        cls.models = Models

    def setup_method(self):
        super().setup_method()
        # Create test users with different URL formats
        self.users.insert_new_user(
            id="test_user_http",
            name="Test User HTTP",
            email="test_http@example.com",
            profile_image_url="http://example.com/image.png",
            role="user",
        )
        self.users.insert_new_user(
            id="test_user_https",
            name="Test User HTTPS",
            email="test_https@example.com",
            profile_image_url="https://example.com/image.png",
            role="user",
        )
        self.users.insert_new_user(
            id="test_user_relative",
            name="Test User Relative",
            email="test_relative@example.com",
            profile_image_url="/static/user.png",
            role="user",
        )
        self.users.insert_new_user(
            id="test_user_base64",
            name="Test User Base64",
            email="test_base64@example.com",
            profile_image_url="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            role="user",
        )

    def test_user_profile_image_http_url(self):
        """Test that HTTP URLs are redirected"""
        with mock_webui_user(id="test_user_http"):
            response = self.fast_api_client.get(
                self.create_url("/test_user_http/profile/image")
            )
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["Location"] == "http://example.com/image.png"

    def test_user_profile_image_https_url(self):
        """Test that HTTPS URLs are redirected"""
        with mock_webui_user(id="test_user_https"):
            response = self.fast_api_client.get(
                self.create_url("/test_user_https/profile/image")
            )
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["Location"] == "https://example.com/image.png"

    def test_user_profile_image_relative_url(self):
        """Test that relative URLs are redirected (this is the new behavior)"""
        with mock_webui_user(id="test_user_relative"):
            response = self.fast_api_client.get(
                self.create_url("/test_user_relative/profile/image")
            )
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["Location"] == "/static/user.png"

    def test_user_profile_image_base64(self):
        """Test that base64 data URLs are properly decoded and returned"""
        with mock_webui_user(id="test_user_base64"):
            response = self.fast_api_client.get(
                self.create_url("/test_user_base64/profile/image")
            )
        # Should return the decoded image, not a redirect
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "image/png"
