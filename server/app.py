# app.py
from functools import wraps
import os
from flask import (
    Flask,
    redirect,
    request,
    send_from_directory,
    jsonify,
    make_response,
    url_for,
)
from authlib.integrations.flask_client import OAuth
import jwt

app = Flask(__name__, static_folder="../web/dist", static_url_path="/")
app.config.from_object("config.Config")

oauth = OAuth(app)
oauth.register(
    "provider",
    request_token_params={"scope": "openid email profile"},
    request_token_url=None,
    access_token_method="POST",
)
provider = oauth.create_client("provider")


def is_token_valid(token):
    jwks_client = jwt.PyJWKClient(app.config["JWKS_URL"])
    header = jwt.get_unverified_header(token)
    try:
        key = jwks_client.get_signing_key(header["kid"]).key
        jwt.decode(token, key, [header["alg"]], options={"verify_aud": False})
    except:
        # The token is invalid or expired
        return False

    return True


def with_valid_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        access_token = request.cookies.get("oauth_access_token")
        if access_token is None:
            return jsonify({"error": "Unauthorized"}), 401

        if is_token_valid(access_token):
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return decorated


@app.route("/oauth/start")
def oauth_start():
    redirect_uri = redirect_uri = url_for("oauth_callback", _external=True)
    print(redirect_uri)
    return provider.authorize_redirect(redirect_uri)


@app.route("/oauth/callback")
def oauth_callback():
    token = provider.authorize_access_token()

    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")

    resp = make_response(redirect("/"))
    resp.set_cookie(
        "oauth_access_token", access_token, httponly=True, samesite="Strict"
    )

    if refresh_token:
        resp.set_cookie(
            "oauth_refresh_token", refresh_token, httponly=True, samesite="Strict"
        )

    return resp


@app.route("/oauth/refresh")
def oauth_refresh_token():
    refresh_token = request.cookies.get("oauth_refresh_token")
    if refresh_token is None:
        return jsonify({"error": "Unauthorized"}), 400

    token = provider.fetch_access_token(
        refresh_token=refresh_token, grant_type="refresh_token"
    )
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")

    resp = make_response(jsonify({"access_token": access_token}))
    resp.set_cookie(
        "oauth_access_token", access_token, httponly=True, samesite="Strict"
    )

    if refresh_token:
        resp.set_cookie(
            "oauth_refresh_token", refresh_token, httponly=True, samesite="Strict"
        )

    return resp


@app.route("/oauth/logout")
def oauth_logout():
    resp = make_response(redirect("/"))
    resp.set_cookie("oauth_access_token", "", expires=0)
    resp.set_cookie("oauth_refresh_token", "", expires=0)
    return resp


@app.route("/secured_resource")
@with_valid_token
def secured_resource():
    return jsonify(
        {
            "message": "This is a secured resource. You should not see this message if you are not authenticated."
        }
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path>")
def serve(path):
    if path != "" and os.path.exists(app.static_folder + "/" + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(debug=True)
