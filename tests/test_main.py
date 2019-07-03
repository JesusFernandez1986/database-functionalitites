import os
import pytest
from main import app, db
from models import User, db


@pytest.fixture
def client():
    app.config['TESTING'] = True
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    client = app.test_client()

    cleanup()  # clean up before every test

    db.create_all()

    yield client


def cleanup():
    # clean up/delete the DB (drop all tables in the database)
    db.drop_all()


def test_index_not_logged_in(client):
    response = client.get('/')
    assert b'Enter your name' in response.data
    assert response.status_code == 200  # 200 means success. See: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes



def test_index_logged_in(client):
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    response = client.get('/')
    assert b'Enter your guess' in response.data


def test_result_guess(client):      #comprobamos si cuando introducimos el guees number hay una respuesta, tanto para acierto como para fallo
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    response = client.post("/", data={"guess": 31})
    assert b"ERROR: El numero no puede ser menor que 1 o mayor que 30" in response.data
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    response = client.post("/", data={"guess": 20,})
    assert b"Demasiado" in response.data or b"Acertaste" in response.data



def test_create_user_ok(client):    #comprobamos que cuando instanciamos el objeto user nos devuelve true
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    response = db.query(User).filter_by(email="test@user.com").count()
    assert response == 1



def test_edit_profile_ok(client):       #comprobar mensajes cuando editamos el perfil
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    response = client.post("/edit_profile", data={"profile-name": "test profile", "new_password": "12345678"}, follow_redirects=True)
    assert b"Your password had been updated" in response.data



def test_delete_profile(client):        #comprobamos que el usario se borra correctamete
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    response = client.post("/delete")
    assert b"Your profile has been deleted succesfully" in response.data



def test_userlist_noshow_deleteprofiles(client):   #comprobamos que los usuarios borrados(inactivos) no salgan en la user list
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    client.post("/delete")
    response = client.get("/user_list")
    assert b"Test User" not in response.data











