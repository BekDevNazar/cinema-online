import pytest
import pytest_asyncio

from models.movie import Movie


@pytest_asyncio.fixture
async def movie(db_session):
    movie = Movie(
        title="Review Test Movie",
        description="Movie for testing reviews",
        release_year=2020,
        duration_minutes=120,
        rating=0.0,
        genre="drama",
        poster_url="https://example.com/poster.jpg",
    )

    db_session.add(movie)
    await db_session.flush()

    return movie


async def get_auth_headers(
    client,
    username="review_user",
    email="review@example.com"
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


# 1. Получение пустого списка отзывов
@pytest.mark.asyncio
async def test_get_reviews_empty(client, movie):
    response = await client.get(
        f"/movies/{movie.id}/reviews/"
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_review(client, db_session, movie):
    headers = await get_auth_headers(client)

    response = await client.post(
        f"/movies/{movie.id}/reviews/",
        json={
            "text": "Great movie!",
            "rating": 8.0
        },
        headers=headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["text"] == "Great movie!"
    assert data["rating"] == 8.0

    await db_session.refresh(movie)

    assert movie.rating == 8.0


@pytest.mark.asyncio
async def test_create_review_without_token(client, movie):
    response = await client.post(
        f"/movies/{movie.id}/reviews/",
        json={
            "text": "Good movie",
            "rating": 7.0
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_review(client, movie):
    headers = await get_auth_headers(client)

    url = f"/movies/{movie.id}/reviews/"

    review_data = {
        "text": "First review",
        "rating": 8.0
    }

    first = await client.post(
        url,
        json=review_data,
        headers=headers
    )

    second = await client.post(
        url,
        json=review_data,
        headers=headers
    )

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_update_review(client, movie):
    headers = await get_auth_headers(client)

    created = await client.post(
        f"/movies/{movie.id}/reviews/",
        json={
            "text": "Good",
            "rating": 7.0
        },
        headers=headers
    )

    assert created.status_code == 201

    review_id = created.json()["id"]

    response = await client.patch(
        f"/movies/{movie.id}/reviews/{review_id}/",
        json={
            "text": "Excellent",
            "rating": 9.0
        },
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["text"] == "Excellent"
    assert data["rating"] == 9.0


@pytest.mark.asyncio
async def test_delete_review(client, db_session, movie):
    headers = await get_auth_headers(client)

    created = await client.post(
        f"/movies/{movie.id}/reviews/",
        json={
            "text": "Nice",
            "rating": 6.0
        },
        headers=headers
    )

    assert created.status_code == 201

    review_id = created.json()["id"]

    response = await client.delete(
        f"/movies/{movie.id}/reviews/{review_id}/",
        headers=headers
    )

    assert response.status_code == 204

    await db_session.refresh(movie)

    assert movie.rating == 0.0


@pytest.mark.asyncio
async def test_cannot_edit_other_users_review(client, movie):
    author_headers = await get_auth_headers(client)

    created = await client.post(
        f"/movies/{movie.id}/reviews/",
        json={
            "text": "My review",
            "rating": 8.0
        },
        headers=author_headers
    )

    assert created.status_code == 201

    review_id = created.json()["id"]

    other_headers = await get_auth_headers(
        client,
        username="another_user",
        email="another@example.com"
    )

    response = await client.patch(
        f"/movies/{movie.id}/reviews/{review_id}/",
        json={
            "text": "Hacked review",
            "rating": 1.0
        },
        headers=other_headers
    )

    assert response.status_code == 403

