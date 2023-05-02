import os
import pathlib
import requests
from flask import Flask, redirect, request, session, abort, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

app = Flask("Google Login App")
app.secret_key = "CoryWuTestApp"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "68387694488-npbracslonpn776e7lbmnjbenbvojnts.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")


flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)
        else:
            return function()       
    return wrapper
        

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/protected_area")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/")
def index():
    return '''<html>
  <head>
    <meta charset="utf-8">
    <title>Login Page</title>
    <style>
      .center {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
      }
      .button {
        display: inline-block;
        padding: 10px 20px;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        text-decoration: none;
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        transition: background-color 0.3s ease;
      }
      .button:hover {
        background-color: #3e8e41;
      }
    </style>
  </head>
  <body>
    <div class="center">
      <a href='/login' class="button">Login</a>
    </div>
  </body>
</html>
'''

@app.route("/protected_area")
@login_is_required
def protected_area():
    return "Protected! <a href='/logout'><button>Logout</button></a>"

if __name__ == "__main__":
    app.run(debug=True)