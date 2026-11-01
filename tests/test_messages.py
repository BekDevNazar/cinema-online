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
async def test_send_message(client):
    sender_id, headers = await create_test_user(
        client, "sender", "sender@example.com"
    )

    receiver_id, _ = await create_test_user(
        client, "receiver", "receiver@example.com"
    )

    response = await client.post(
        f"/users/{receiver_id}/messages/",
        json={"text": "Hello!"},
        headers=headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["text"] == "Hello!"
    assert data["sender_id"] == sender_id
    assert data["receiver_id"] == receiver_id
    assert data["is_read"] is False


@pytest.mark.asyncio
async def test_get_messages(client):
    user1_id, headers1 = await create_test_user(
        client, "user1", "user1@example.com"
    )

    user2_id, headers2 = await create_test_user(
        client, "user2", "user2@example.com"
    )

    first = await client.post(
        f"/users/{user2_id}/messages/",
        json={"text": "Hello!"},
        headers=headers1
    )

    assert first.status_code == 201

    second = await client.post(
        f"/users/{user1_id}/messages/",
        json={"text": "Hi!"},
        headers=headers2
    )

    assert second.status_code == 201

    response = await client.get(
        f"/users/{user2_id}/messages/",
        headers=headers1
    )

    assert response.status_code == 200

    messages = response.json()

    assert len(messages) == 2
    assert messages[0]["text"] == "Hello!"
    assert messages[1]["text"] == "Hi!"

    chats = await client.get(
        "/users/me/conversations/",
        headers=headers1
    )

    assert chats.status_code == 200
    assert len(chats.json()) == 1
    assert chats.json()[0]["user_id"] == user2_id
    assert chats.json()[0]["last_message"] == "Hi!"


@pytest.mark.asyncio
async def test_send_message_without_auth(client):
    receiver_id, _ = await create_test_user(
        client, "receiver", "receiver@example.com"
    )

    response = await client.post(
        f"/users/{receiver_id}/messages/",
        json={"text": "Hello!"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_send_message_to_self(client):
    user_id, headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    response = await client.post(
        f"/users/{user_id}/messages/",
        json={"text": "Hello myself!"},
        headers=headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "You can't send a message to yourself"
    )


@pytest.mark.asyncio
async def test_send_message_user_not_found(client):
    _, headers = await create_test_user(
        client, "sender", "sender@example.com"
    )

    response = await client.post(
        "/users/999999999/messages/",
        json={"text": "Hello!"},
        headers=headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_messages_are_private(client):
    user1_id, headers1 = await create_test_user(
        client, "user1", "user1@example.com"
    )

    user2_id, _ = await create_test_user(
        client, "user2", "user2@example.com"
    )

    _, headers3 = await create_test_user(
        client, "user3", "user3@example.com"
    )

    sent = await client.post(
        f"/users/{user2_id}/messages/",
        json={"text": "Private message"},
        headers=headers1
    )

    assert sent.status_code == 201

    response = await client.get(
        f"/users/{user2_id}/messages/",
        headers=headers3
    )

    assert response.status_code == 200

    assert response.json() == []

    response = await client.get(
        f"/users/{user1_id}/messages/",
        headers=headers3
    )

    assert response.status_code == 200
    assert response.json() == []
