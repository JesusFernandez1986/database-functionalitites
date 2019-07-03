from flask import Flask, render_template, request, redirect, url_for, make_response
from models import User, db
import random
import hashlib
import uuid

app = Flask(__name__)
db.create_all()

wrong_guess = []


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")        #cogemos del formulario el nombre y el email y los guardamos en las variables name y email
    email = request.form.get("user-email")
    secret_number = random.randint(1, 30)       #generamos un numero aleatorio y lo guardamos en secret_number
    password = request.form.get("user-password")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()     #encriptamos el password

    user = db.query(User).filter_by(email=email).first()    #comprobamos si ese usuario existe en nuestra base de datos, filtrando por el email

    if not user:                                #si no hay un usuario registrado, creamos una instancia nueva para ese usuario y la guardamos en la bsae de datos
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password,)
        db.add(user)
        db.commit()

    if hashed_password != user.password:
        return "WRONG PASSWORD! Go back and try again."
    elif hashed_password == user.password:             #si el password introducido es igual al de la base de datos generamos un numero de sesion y lo guardamos en la BD
        session_token = str(uuid.uuid4())
        user.session_token = session_token
        db.add(user)
        db.commit()

    response = make_response(redirect(url_for('index')))
    response.set_cookie("session_token", session_token, httponly=True, samesite='Strict')       #guardamos el token de sesions en una cookie llamada session_token
    return response



@app.route("/logout")
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie("session_token", expires=0)
    return response



@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        data = {}
        session_token = request.cookies.get("session_token")                        #guardamos el valor de la cookie session token en la variable session_token

        if session_token:
            user = db.query(User).filter_by(session_token=session_token).first()  #si tenemos una session token, miramos y comparamos en la base de datos
        else:                                                                       #si no creamos una instancia user vacia
            user = None

        data.update({'user': user})
        message = request.args.get("message", False)                            #cogemos el mensaje enviado por /profile y /user_list
        return render_template("index.html", data=data, message=message)

    elif request.method == "POST":
        guess = request.form.get('guess', False)
        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

        try:                    # compara si el valor introducido es un entero y si no lo es devuelve un error
            guess = int(guess)
        except Exception:
            data = {'result': False,
                    "user": user,
                    "error": 2}
            response = make_response(render_template("index.html", data=data))
            return response

        if guess > 30 or guess < 1:    #comprueba que ademas de ser un entero sea un valor comprendido entre 1 y 30, si no devuelve un error
            data = {'result': False,
                    "user": user,
                    "error": 1}
            response = make_response(render_template("index.html", data=data))
            return response

        if guess == int(user.secret_number):    # Si ha acertado:
            new_secret = random.randint(1, 30)
            user.secret_number = new_secret
            db.add(user)
            db.commit()
            new_wrong = wrong_guess.copy()
            data = {'result': True,
                    "wrong_guess": new_wrong,
                    "user": user}
            wrong_guess.clear()
            response = make_response(render_template("index.html", data=data))
            return response
        else:                              # Si no hemos acertado damos una pista para que pueda acertar
            if int(user.secret_number) < guess:
                data = {'result': False, # Diferentes lineas para mas orden y solo un diccionario con datos
                        'hint': "Demasiado grande, prueba algo mas pequeño",
                        'user': user}
            else:
                data = {'result': False,
                        'hint': "Demasiado pequeño, prueba algo mas grande",
                        'user': user}
            response = make_response(render_template("index.html", data=data))
            wrong_guess.append(guess)
        return response     # Devolvemos  un response por pantalla,mostrando un mensaje segun si ha acertado o si ha puesto un numero mayor o menor
    return render_template("index.html")


@app.route("/profile")
def profile():
    session_token = request.cookies.get("session_token", False)
    if not session_token:
        message = "You need to be logged in to access"
        return redirect(url_for("index", message=message))

    user = db.query(User).filter_by(session_token=session_token).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))



@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        return render_template("edit_profile.html", user=user)
    elif request.method == "POST":
        name = request.form.get("profile-name")     #cogemos el nombre y el email del formulario y lo guardamos en estas variables
        email = request.form.get("profile-email")
        new_password = request.form.get("new_password")

        if len(new_password) >= 6:
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
            if hashed_new_password != user.password:
                user.password = hashed_new_password
                message = "Your password had been updated succesfully"
            else:
                message1 = "This password is the same than the old one, please set a different one"
                return render_template("edit_profile.html", message1=message1, user=user)
        else:
            message2 = "Your password must be at least 6 characters long"
            return render_template("edit_profile.html", message2=message2, user=user)

        user.name = name            #asignamos el valor de la variable name y email a la propiedad user.name y user.email del objeto
        user.email = email
        db.add(user)                #guardamos los cambios en la base de datos
        db.commit()

        return render_template("profile.html", message=message, user=user)



@app.route("/delete", methods=["GET", "POST"])
def delete():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        return render_template("delete.html", user=user)

    elif request.method == "POST":
        if not user.inactive:
            message3 = "Your profile has been deleted succesfully"
            user.inactive = True
            db.add(user)
            db.commit()
            resp = make_response(render_template("profile.html", user=user, message3=message3))
            resp.set_cookie('session_token', expires=0)
            return resp
        else:
            redirect(url_for("profile"))



@app.route("/users_list", methods=["GET"])
def users_list():
    users = db.query(User).filter_by(inactive=False).all()
    session_token = request.cookies.get("session_token", False)
    if not session_token:
        message = "You need to be logged in to access"
        return redirect(url_for("index", message=message))
    return render_template("users.html", users=users)



@app.route("/user/<user_id>", methods=["GET"])
def user_details(user_id):
    user = db.query(User).get(int(user_id))
    return render_template("user_details.html", user=user)



if __name__ == '__main__':
    app.run(debug=True)
