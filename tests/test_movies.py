import pytest

from sqlalchemy import select
from models.movie import Movie
from types import SimpleNamespace

from main import app
from dependencies import get_current_user


movie_data = {
    "title": "Interstellar",
    "description": "Science fiction movie",
    "release_year": 2014,
    "duration_minutes": 169,
    "rating": 8.5,
    "genre": "sci-fi",
    "poster_url": "https://example.com/poster.jpg"
}


@pytest.mark.asyncio
async def test_get_movies(client):
    response = await client.get("/movies/")

    assert response.status_code == 200

    data = response.json()

    assert "movies" in data
    assert isinstance(data["movies"], list)
    assert data["page"] == 1
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_get_movie_not_found(client):
    response = await client.get("/movies/999999999/")

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Movie not found"


@pytest.mark.asyncio
async def test_get_movies_invalid_page(client):
    response = await client.get("/movies/?page=0")

    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], list)


@pytest.mark.asyncio
async def test_create_movie_without_auth(client):
    response = await client.post(
        "/movies/",
        json=movie_data
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_create_movie_invalid_token(client):
    response = await client.post(
        "/movies/",
        json=movie_data,
        headers={
            "Authorization": "Bearer invalid_token_123"
        }
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_create_movie_forbidden(client):
    async def override_get_current_user():
        return SimpleNamespace(role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        response = await client.post(
            "/movies/",
            json=movie_data
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "You are not admin"

    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_movie_as_admin(client, db_session):
    async def override_get_current_user():
        return SimpleNamespace(role="admin")

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        response = await client.post(
            "/movies/",
            json=movie_data
        )

        assert response.status_code == 201

        data = response.json()

        assert data["title"] == "Interstellar"
        assert "id" in data

        result = await db_session.execute(
            select(Movie).where(Movie.id == data["id"])
        )

        movie = result.scalar_one_or_none()

        assert movie is not None
        assert movie.title == "Interstellar"

    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_movie_as_admin(client, db_session):
    async def override_get_current_user():
        return SimpleNamespace(role="admin")

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        create_response = await client.post(
            "/movies/",
            json=movie_data
        )

        assert create_response.status_code == 201

        movie_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/movies/{movie_id}/",
            json={"title": "Interstellar Updated"}
        )

        assert update_response.status_code == 200

        data = update_response.json()

        assert data["title"] == "Interstellar Updated"
        assert data["duration_minutes"] == 169

        movie = await db_session.get(Movie, movie_id)

        assert movie is not None

        await db_session.refresh(movie)

        assert movie.title == "Interstellar Updated"
        assert movie.duration_minutes == 169

    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_movie_as_admin(client, db_session):
    async def override_get_current_user():
        return SimpleNamespace(role="admin")

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        create_response = await client.post(
            "/movies/",
            json=movie_data
        )

        assert create_response.status_code == 201

        movie_id = create_response.json()["id"]

        delete_response = await client.delete(
            f"/movies/{movie_id}/"
        )

        assert delete_response.status_code == 204

        get_response = await client.get(
            f"/movies/{movie_id}/"
        )

        assert get_response.status_code == 404
        assert get_response.json()["detail"] == "Movie not found"

        deleted_movie = await db_session.get(Movie, movie_id)

        assert deleted_movie is None

    finally:
        app.dependency_overrides.pop(get_current_user, None)
