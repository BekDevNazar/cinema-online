
import pytest
from sqlalchemy import select, func

from models.user import User


user_data = {
        "username": "test_user",
        "email": "testuser@example.com",
        "password": "StrongPassword123!"
    }


@pytest.mark.asyncio
async def test_register_user(client, db_session):
    response = await client.post(
        "/auth/register",
        json=user_data
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

    result = await db_session.execute(
        select(User).where(User.email == user_data["email"])
    )

    user = result.scalar_one_or_none()

    assert user is not None
    assert user.username == user_data["username"]

    assert user.password_hash != user_data["password"]
    assert user.password_hash


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db_session):
    first_user = {
        "username": "test_user1",
        "email": "duplicate@example.com",
        "password": "StrongPassword123!"
    }

    second_user = {
        "username": "test_user2",
        "email": "duplicate@example.com",
        "password": "AnotherPassword123!"
    }
    response_1 = await client.post(
        "/auth/register",
        json=first_user
    )
    assert response_1.status_code == 201
    response_2 = await client.post(
        "/auth/register",
        json=second_user
    )
    assert response_2.status_code == 409

    count = await db_session.scalar(
        select(func.count(User.id)).where(
            User.email == "duplicate@example.com"
        )
    )
    assert count == 1


@pytest.mark.asyncio
async def test_login_success(client):
    response = await client.post(
        "/auth/register",
        json=user_data
    )

    assert response.status_code == 201

    login_response = await client.post(
        "/auth/login/",
         json={
             "email": "testuser@example.com",
             "password": "StrongPassword123!"
         }
    )
    assert login_response.status_code == 200

    data = login_response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0

    assert "refresh_token" in data
    assert isinstance(data["refresh_token"], str)
    assert len(data["refresh_token"]) > 0



@pytest.mark.asyncio
async def test_login_invalid_password(client):
    register_response = await client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login/",
        json={
            "email": user_data["email"],
            "password": "WrongPassword123!"
        }
    )

    assert login_response.status_code == 401

    data = login_response.json()

    assert "detail" in data
    assert isinstance(data["detail"], str)

    assert "access_token" not in data
    assert "refresh_token" not in data


@pytest.mark.asyncio
async def test_get_me(client):
    register_response = await client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login/",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    assert me_response.status_code == 200
    data = me_response.json()

    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]


@pytest.mark.asyncio
async def test_get_me_without_token(client):
    response = await client.get("/auth/me")

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired token"



@pytest.mark.asyncio
async def test_refresh_token(client):
    register_response = await client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login/",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )

    assert login_response.status_code == 200

    login_data = login_response.json()
    old_refresh_token = login_data["refresh_token"]

    refresh_response = await client.post(
        "/auth/refresh/",
        json={
            "refresh_token": old_refresh_token
        }
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert "access_token" in refresh_data
    assert isinstance(refresh_data["access_token"], str)
    assert len(refresh_data["access_token"]) > 0

    assert "refresh_token" in refresh_data

    new_refresh_token = refresh_data["refresh_token"]

    assert isinstance(new_refresh_token, str)
    assert len(new_refresh_token) > 0
    assert new_refresh_token != old_refresh_token

    me_response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {refresh_data['access_token']}"
        }
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == user_data["email"]

    reuse_response = await client.post(
        "/auth/refresh/",
        json={
            "refresh_token": old_refresh_token
        }
    )

    assert reuse_response.status_code == 401



@pytest.mark.asyncio
async def test_logout(client):
    register_response = await client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login/",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    logout_response = await client.post(
        "/auth/logout/",
        json={
            "refresh_token": refresh_token
        }
    )

    assert logout_response.status_code == 200

    refresh_response = await client.post(
        "/auth/refresh/",
        json={
            "refresh_token": refresh_token
        }
    )

    assert refresh_response.status_code == 401

    second_logout_response = await client.post(
        "/auth/logout/",
        json={
            "refresh_token": refresh_token
        }
    )

    assert second_logout_response.status_code == 400
