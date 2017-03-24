"""Dungeons & Dragons character sheet app."""
from pathlib import Path
import asyncio
from pkg_resources import resource_filename, Requirement, cleanup_resources
# import uvloop
from aiohttp import web
import aiohttp_jinja2
import jinja2
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_login
from aiohttp_login.motor_storage import MotorStorage

from user_config import (
    Config, Section, StringOption, IntegerOption, BooleanOption)
from roman import toRoman

from dnd.views.index import index_handler, new_character_data_handler
from dnd.views.character import character_handler, data_handler

class DndConfiguration(Config):

    """Configuration for dnd."""

    application = "dnd"
    author = "nihlaeth"

    # pylint: disable=invalid-name
    class ServerSection(Section):

        """Server settings, including session."""

        ip = StringOption(
            doc="IP address to listen on",
            default='0.0.0.0')
        port = IntegerOption(doc="port to listen on", default=8000)
        debug = BooleanOption(
            doc=("debug status, determines verbosity and "
                 "automatic template reloading"),
            default=False)
        session_secret = StringOption(
            doc="44 character ASCII encoded secret")
        session_max_age = IntegerOption(
            doc="maximum age of session in seconds",
            default=315360000)

    server = ServerSection()

    class AuthenticationSection(Section):

        """Settings for aiohttp-login."""

        theme = StringOption(
            doc="theme to use for authentication pages",
            default='auth')
        common_theme = StringOption(
            doc="theme directory for unthemed authentication pages",
            default='common')
        # password_len = IntegerPairOption(default=(6, 10))
        login_redirect = StringOption(
            doc="URL to redirect to after login",
            default='/')
        logout_redirect = StringOption(
            doc="URL to redirect to after logout",
            default='auth_login')
        registration_confirmation_required = BooleanOption(
            doc="require e-mail confirmation after registration?",
            default=True)
        # admin_emails = StringListOption(default=[])
        csrf_secret = StringOption(
            doc="cross site redirect forgery secret")
        back_url_qs_key = StringOption(
            doc="URL key to indicate page to return to",
            default='back_to')
        session_user_key = StringOption(
            doc="key for user field in session",
            default='user')
        request_user_key = StringOption(
            doc="key for user field in request",
            default='user')
        session_flash_key = StringOption(
            doc="key for flash messages field in session",
            default='flash')
        request_flash_incoming_key = StringOption(
            doc="key for incoming flash messages in request",
            default='flash_incoming')
        request_flash_outgoing_key = StringOption(
            doc="key for outgoing flash messages in request",
            default='flash_outgoing')
        flash_queue_limit = IntegerOption(
            doc="maximum number of flash messages in queue",
            default=10)
        vkontakte_id = StringOption(
            doc="id for the vkontakte authentication service",
            required=False)
        vkontakte_secret = StringOption(
            doc="secret for the vkontakte authentication service",
            required=False)
        google_id = StringOption(
            doc="id for the google authentication service",
            required=False)
        google_secret = StringOption(
            doc="secret for the google authentication service",
            required=False)
        facebook_id = StringOption(
            doc="id for the facebook authentication service",
            required=False)
        facebook_secret = StringOption(
            doc="secret for the facebook authentication service",
            required=False)
        smtp_sender = StringOption(
            doc="content of the from header field for e-mail",
            required=False)
        smtp_host = StringOption(doc="address of your SMTP server")
        smtp_port = IntegerOption(
            doc="port of your SMTP server",
            default=587)
        smtp_tls = BooleanOption(
            doc="use transport layer security",
            default=True)
        smtp_username = StringOption(
            doc="SMTP username",
            required=False)
        smtp_password = StringOption(
            doc="SMTP password",
            required=False)
        registration_confirmation_lifetime = IntegerOption(
            doc="number of days before a registration confirmation link expires",
            default=5)
        reset_password_confirmation_lifetime = IntegerOption(
            doc="number of days before a password reset link expires",
            default=5)
        change_email_confirmation_lifetime = IntegerOption(
            doc="number of days before an e-mail change confirmation link expires",
            default=5)

        msg_logged_in = StringOption(
            doc="message to display on successful login",
            default='You are logged in')
        msg_logged_out = StringOption(
            doc="message to display after logout",
            default='You are logged out')
        msg_activated = StringOption(
            doc="message to display on successful account activation",
            default='Your account is activated')
        msg_unknown_email = StringOption(
            doc="message to display if e-mail is not registered",
            default='This email is not registered')
        msg_wrong_password = StringOption(
            doc="message to display if password is incorrect",
            default='Wrong password')
        msg_user_banned = StringOption(
            doc="message to display of banned user tries to login",
            default='This user is banned')
        msg_activation_required = StringOption(
            doc="message to display if e-mail has not been verified",
            default=(
                'You have to activate your account via'
                ' email, before you can login'))
        msg_email_exists = StringOption(
            doc="message to display a e-mail is already registered",
            default='This email is already registered')
        msg_often_reset_password = StringOption(
            doc=("message to display if password restoration has "
                 "already been requested"),
            default=(
                'You can\'t request restoring your password so often. '
                'Please, use the link we sent you recently'))
        msg_cant_send_mail = StringOption(
            doc="message to display if there is a problem sending e-mail",
            default='Can\'t send email, try a little later')
        msg_passwords_not_match = StringOption(
            doc="message to display if passwords don't match",
            default='Passwords must match')
        msg_password_changed = StringOption(
            doc="message to display after successful password change",
            default='Your password is changed')
        msg_change_email_requested = StringOption(
            doc=("message to display after e-mail change has been "
                 "requested, but not verified"),
            default=(
                'Please, click on the verification link'
                ' we sent to your new email address'))
        msg_email_changed = StringOption(
            doc="message to display after e-mail change has been verified",
            default='Your email is changed')
        msg_auth_failed = StringOption(
            doc="message to display if authorisation failed",
            default='Authorization failed')

    authentication = AuthenticationSection()

def start():
    """Start Web server."""
    config = DndConfiguration()
    # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    app = web.Application(debug=config.server.debug)
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(resource_filename(
            Requirement.parse('dnd'), 'dnd/templates')),
        auto_reload=config.server.debug,
        context_processors=[aiohttp_login.flash.context_processor])
    aiohttp_session.setup(app, EncryptedCookieStorage(
        config.server.session_secret,
        max_age=config.server.session_max_age))
    aiohttp_jinja2.get_env(app).filters['to_roman'] = toRoman
    app.middlewares.append(aiohttp_login.flash.middleware)

    app['db_client'] = AsyncIOMotorClient()
    app['db'] = app['db_client'].dnd

    auth_settings = {}
    for setting in config.authentication:
        auth_settings[setting.upper()] = config.authentication[setting]
    aiohttp_login.setup(app, MotorStorage(app['db']), auth_settings)

    app.router.add_static(
        "/static/",
        path=Path(__file__) / ".." / "static",
        name="static")
    app.router.add_get("/", index_handler)
    app.router.add_post("/api/new-character/", new_character_data_handler)
    app.router.add_get("/{id}/{name}/", character_handler)
    app.router.add_post(
        "/api/{id}/{attribute}/{extra}/", data_handler)
    app.router.add_post("/api/{id}/{attribute}/", data_handler)
    web.run_app(app, host=config.server.ip, port=config.server.port)
    cleanup_resources()
