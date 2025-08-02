from fastapi import status


def test_create_user(client):
    response = client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['username'] == 'alice'
    assert data['email'] == 'alice@example.com'
    assert 'id' in data  # Verifica apenas se o ID existe


def test_read_users(client):
    response = client.get('/users')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'users': []}


def test_read_users_with_users(client, user):
    response = client.get('/users/')
    data = response.json()
    assert len(data['users']) == 1
    user_data = data['users'][0]
    assert user_data['username'] == user.username
    assert user_data['email'] == user.email
    assert 'id' in user_data  # Verifica apenas se o ID existe


def test_update_user(client, user, token):
    response = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['username'] == 'bob'
    assert data['email'] == 'bob@example.com'
    assert data['id'] == str(user.id)


def test_update_integrity_error(client, user, token):
    # Inserindo fausto
    client.post(
        '/users',
        json={
            'username': 'fausto',
            'email': 'fausto@example.com',
            'password': 'secret',
        },
    )

    # Alterando o user das fixture para fausto
    response_update = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )

    assert response_update.status_code == status.HTTP_409_CONFLICT
    assert response_update.json() == {
        'detail': 'Username or Email already exists'
    }


def test_delete_user(client, user, token):
    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message': 'User deleted'}


def test_update_user_with_wrong_user(client, other_user, token):
    response = client.put(
        f'/users/{other_user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}


def test_delete_user_wrong_user(client, other_user, token):
    response = client.delete(
        f'/users/{other_user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}
