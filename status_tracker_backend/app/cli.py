from flask.cli import with_appcontext
import click
from .extensions import db


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize database by creating all tables."""
    db.create_all()
    click.echo("Database initialized.")
