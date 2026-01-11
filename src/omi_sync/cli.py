"""Omi to Obsidian sync CLI."""
import click
from dotenv import load_dotenv

# Load .env file if present (looks in current directory and parents)
load_dotenv()


@click.group()
def main():
    """Sync Omi conversations to Obsidian vault."""
    pass


@main.command()
def run():
    """Run one-shot sync."""
    from omi_sync.config import load_config, ConfigError
    from omi_sync.api_client import OmiClient, OmiAPIError
    from omi_sync.sync_engine import SyncEngine

    try:
        config = load_config()
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"Syncing to vault: {config.vault_path}")

    try:
        with OmiClient(config.api_key, config.api_base_url) as client:
            api_data = client.fetch_all_conversations()

        click.echo(f"Fetched {len(api_data)} conversations from API")

        engine = SyncEngine(config)
        result = engine.sync(api_data)

        stats = result["stats"]
        click.echo(f"Processed {stats['dates']} date(s)")
        click.echo(f"  Raw files: {stats['raw_files']}")
        click.echo(f"  Event files: {stats['event_files']}")
        click.echo(f"  Highlights files: {stats['highlights_files']}")
        click.echo("DONE")

    except OmiAPIError as e:
        click.echo(f"API Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Sync failed: {e}", err=True)
        raise SystemExit(1)


@main.command()
def doctor():
    """Validate configuration."""
    from omi_sync.config import load_config, ConfigError

    try:
        config = load_config()
        click.echo(f"API Key: {'*' * 8}...{config.api_key[-4:] if len(config.api_key) > 4 else '****'}")
        click.echo(f"Vault Path: {config.vault_path}")
        click.echo(f"API URL: {config.api_base_url}")
        click.echo(f"Timezone: {config.timezone}")
        click.echo(f"Finalization Lag: {config.finalization_lag_minutes} minutes")
        click.echo(f"Notable Duration: {config.notable_duration_minutes} minutes")
        click.echo(f"Notable Action Items Min: {config.notable_action_items_min}")
        click.echo("Configuration OK")
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)


@main.command("rebuild-index")
def rebuild_index():
    """Rebuild index from vault frontmatter."""
    from omi_sync.config import load_config, ConfigError
    from omi_sync.rebuild import rebuild_index_from_vault

    try:
        config = load_config()
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"Scanning vault: {config.vault_path}")
    count = rebuild_index_from_vault(config)
    click.echo(f"Rebuilt index with {count} entries")


if __name__ == "__main__":
    main()
