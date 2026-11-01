import pytest


async def create_test_user(client, username, email):
    user_data = {
        "username": username,
        "email": email,
        "password": "StrongPassword123!"
    }

    register = await client.post(
        "/auth/register",
        json=user_data
    )
    assert register.status_code == 201

    user_id = register.json()["id"]

    login = await client.post(
        "/auth/login/",
        json={
            "email": email,
            "password": user_data["password"]
        }
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    return user_id, headers


@pytest.mark.asyncio
async def test_get_empty_notifications(client):
    _, headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    response = await client.get(
        "/users/me/notifications/",
        headers=headers
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_follow_notification(client):
    _, follower_headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    target_id, target_headers = await create_test_user(
        client, "user2", "user2@example.com"
    )

    follow = await client.post(
        f"/users/{target_id}/follow/",
        headers=follower_headers
    )

    assert follow.status_code == 201

    response = await client.get(
        "/users/me/notifications/",
        headers=target_headers
    )

    assert response.status_code == 200

    notifications = response.json()

    assert len(notifications) == 1
    assert notifications[0]["type"] == "new_follower"
    assert notifications[0]["is_read"] is False
    assert "id" in notifications[0]


@pytest.mark.asyncio
async def test_message_notification(client):
    _, sender_headers = await create_test_user(
        client, "sender", "sender@example.com"
    )

    receiver_id, receiver_headers = await create_test_user(
        client, "receiver", "receiver@example.com"
    )

    message = await client.post(
        f"/users/{receiver_id}/messages/",
        json={"text": "Hello!"},
        headers=sender_headers
    )

    assert message.status_code == 201

    response = await client.get(
        "/users/me/notifications/",
        headers=receiver_headers
    )

    assert response.status_code == 200

    notifications = response.json()

    assert len(notifications) == 1
    assert notifications[0]["type"] == "new_message"
    assert notifications[0]["is_read"] is False


@pytest.mark.asyncio
async def test_mark_notification_as_read(client):
    _, follower_headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    target_id, target_headers = await create_test_user(
        client, "user2", "user2@example.com"
    )

    follow = await client.post(
        f"/users/{target_id}/follow/",
        headers=follower_headers
    )
    assert follow.status_code == 201

    response = await client.get(
        "/users/me/notifications/",
        headers=target_headers
    )

    assert response.status_code == 200

    notification_id = response.json()[0]["id"]

    read_response = await client.patch(
        f"/users/me/notifications/{notification_id}/read/",
        headers=target_headers
    )

    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    check_response = await client.get(
        "/users/me/notifications/",
        headers=target_headers
    )

    assert check_response.json()[0]["is_read"] is True


@pytest.mark.asyncio
async def test_cannot_read_other_users_notification(client):
    _, follower_headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    target_id, target_headers = await create_test_user(
        client, "user2", "user2@example.com"
    )

    follow = await client.post(
        f"/users/{target_id}/follow/",
        headers=follower_headers
    )
    assert follow.status_code == 201

    response = await client.get(
        "/users/me/notifications/",
        headers=target_headers
    )

    assert response.status_code == 200

    notification_id = response.json()[0]["id"]

    read_response = await client.patch(
        f"/users/me/notifications/{notification_id}/read/",
        headers=follower_headers
    )

    assert read_response.status_code == 404


@pytest.mark.asyncio
async def test_notifications_without_auth(client):
    response = await client.get(
        "/users/me/notifications/"
    )

    assert response.status_code == 401
