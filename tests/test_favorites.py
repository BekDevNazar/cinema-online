import pytest
import pytest_asyncio

from models.movie import Movie


@pytest_asyncio.fixture
async def movie(db_session):
    movie = Movie(
        title="Test Favorite Movie",
        description="Movie for favorites testing",
        release_year=2020,
        duration_minutes=120,
        rating=0.0,
        genre="drama",
        poster_url="https://example.com/poster.jpg"
    )

    db_session.add(movie)
    await db_session.flush()

    return movie


async def get_auth_headers(
    client,
    username="favorite_user",
    email="favorite@example.com"
):
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

    login = await client.post(
        "/auth/login/",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.mark.asyncio
async def test_add_favorite(client, movie):
    headers = await get_auth_headers(client)

    response = await client.post(
        f"/movies/{movie.id}/favorite/",
        headers=headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["movie_id"] == movie.id
    assert "user_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_add_favorite_without_auth(client, movie):
    response = await client.post(
        f"/movies/{movie.id}/favorite/"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_favorite(client, movie):
    headers = await get_auth_headers(client)

    url = f"/movies/{movie.id}/favorite/"

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
async def test_delete_favorite(client, movie):
    headers = await get_auth_headers(client)

    url = f"/movies/{movie.id}/favorite/"

    add_response = await client.post(
        url,
        headers=headers
    )

    assert add_response.status_code == 201

    delete_response = await client.delete(
        url,
        headers=headers
    )

    assert delete_response.status_code == 204

    second_delete = await client.delete(
        url,
        headers=headers
    )

    assert second_delete.status_code == 404


@pytest.mark.asyncio
async def test_favorite_movie_not_found(client):
    headers = await get_auth_headers(client)

    response = await client.post(
        "/movies/999999999/favorite/",
        headers=headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"


@pytest.mark.asyncio
async def test_cannot_delete_other_users_favorite(client, movie):
    first_headers = await get_auth_headers(client)

    url = f"/movies/{movie.id}/favorite/"

    created = await client.post(
        url,
        headers=first_headers
    )

    assert created.status_code == 201

    second_headers = await get_auth_headers(
        client,
        username="second_user",
        email="second@example.com"
    )

    response = await client.delete(
        url,
        headers=second_headers
    )

    assert response.status_code == 404

    owner_delete = await client.delete(
        url,
        headers=first_headers
    )

    assert owner_delete.status_code == 204
