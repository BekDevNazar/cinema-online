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
async def test_follow_user(client):
    follower_id, headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    target_id, _ = await create_test_user(
        client, "user2", "user2@example.com"
    )

    response = await client.post(
        f"/users/{target_id}/follow/",
        headers=headers
    )

    assert response.status_code == 201

    # Проверяем подписчиков второго пользователя
    followers = await client.get(
        f"/users/{target_id}/followers/"
    )

    assert followers.status_code == 200
    assert len(followers.json()) == 1
    assert followers.json()[0]["id"] == follower_id

    # Проверяем подписки первого пользователя
    following = await client.get(
        f"/users/{follower_id}/following/"
    )

    assert following.status_code == 200
    assert following.json()[0]["id"] == target_id


@pytest.mark.asyncio
async def test_unfollow_user(client):
    _, headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    target_id, _ = await create_test_user(
        client, "user2", "user2@example.com"
    )

    url = f"/users/{target_id}/follow/"

    follow = await client.post(
        url,
        headers=headers
    )

    assert follow.status_code == 201

    unfollow = await client.delete(
        url,
        headers=headers
    )

    assert unfollow.status_code == 204

    followers = await client.get(
        f"/users/{target_id}/followers/"
    )

    assert followers.status_code == 200
    assert followers.json() == []


@pytest.mark.asyncio
async def test_follow_without_auth(client):
    target_id, _ = await create_test_user(
        client, "user2", "user2@example.com"
    )

    response = await client.post(
        f"/users/{target_id}/follow/"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_follow(client):
    _, headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    target_id, _ = await create_test_user(
        client, "user2", "user2@example.com"
    )

    url = f"/users/{target_id}/follow/"

    first = await client.post(
        url,
        headers=headers
    )

    second = await client.post(
        url,
        headers=headers
    )

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_follow_yourself(client):
    user_id, headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    response = await client.post(
        f"/users/{user_id}/follow/",
        headers=headers
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "You can't follow yourself"
    )


@pytest.mark.asyncio
async def test_follow_user_not_found(client):
    _, headers = await create_test_user(
        client, "user1", "user1@example.com"
    )

    response = await client.post(
        "/users/999999999/follow/",
        headers=headers
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "User not found"
