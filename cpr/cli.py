import sys
import click

from cpr.data import DataStore
from cpr.models import build_response

@click.group
def cli() -> None:
    "CPR Keyword search"

@cli.command()
@click.option(
    '--file', '-f', 'data_file',
    required=True,
    metavar="PATH",
)
@click.argument("query")
@click.option("--limit", "-n", default=10)
def search(data_file: str, query: str, limit: int) -> None:
    store = DataStore()
    try:
        store.load(data_file)
    except FileNotFoundError as e:
        click.echo(f"Error file not found: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f'Error loading data: {e}', err=True)
        sys.exit(1)
    results = store.search(query, limit)
    click.echo(build_response(query, results).model_dump_json(indent=2))

if __name__ == "__main__":
    search()
