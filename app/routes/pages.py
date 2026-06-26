from flask import Blueprint, redirect, render_template, url_for

from ..decorators import current_user, login_required

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("pages.login"))
    if not user.onboarding_complete():
        return redirect(url_for("pages.onboarding"))
    return redirect(url_for("pages.seller" if user.user_type == "seller" else "pages.buyer"))


@pages_bp.route("/login")
def login():
    return render_template("start_login.html")


@pages_bp.route("/onboarding")
def onboarding():
    return render_template("phone_input.html")


@pages_bp.route("/buyer")
@login_required(api=False)
def buyer():
    return render_template("home.html")


@pages_bp.route("/seller")
@login_required(api=False)
def seller():
    return render_template("home_bes.html")
