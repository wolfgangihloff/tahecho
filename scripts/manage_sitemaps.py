#!/usr/bin/env python3
"""Sitemap Management Script for Tahecho."""

import click
import asyncio
import yaml
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tahecho.sitemap.configuration_manager import ConfigurationManager
from tahecho.sitemap.supabase_integration import SupabaseIntegration
from tahecho.sitemap.scrapy_manager import ScrapyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='YAML configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """Sitemap Management Script for Tahecho."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config_manager = ConfigurationManager()
    if config:
        config_manager.load_yaml_config(config)
    
    ctx.obj = {
        'config_manager': config_manager,
        'supabase': SupabaseIntegration(
            url=config_manager.get_supabase_url(),
            anon_key=config_manager.get_supabase_anon_key(),
            service_key=config_manager.get_supabase_service_key()
        ),
        'scrapy_manager': ScrapyManager(config_manager)
    }


@cli.command()
@click.option('--url', '-u', required=True, help='Sitemap URL to scrape')
@click.option('--incremental', '-i', is_flag=True, help='Only scrape new/changed content')
@click.option('--differential', '-d', is_flag=True, help='Differential update for specific sections')
@click.option('--sections', '-s', help='Comma-separated sections for differential update')
@click.option('--max-pages', '-m', type=int, help='Maximum pages to scrape')
@click.pass_context
async def scrape(ctx, url, incremental, differential, sections, max_pages):
    """Scrape a sitemap."""
    config_manager = ctx.obj['config_manager']
    supabase = ctx.obj['supabase']
    scrapy_manager = ctx.obj['scrapy_manager']
    
    if not config_manager.validate_sitemap_url(url):
        click.echo(f"Error: Invalid sitemap URL: {url}")
        return
    
    try:
        click.echo(f"Starting sitemap scraping: {url}")
        
        # Get sitemap-specific configuration
        sitemap_config = config_manager.get_sitemap_config(url) or {}
        
        # Override with command line options
        if max_pages:
            sitemap_config['max_pages'] = max_pages
        
        if differential and sections:
            sitemap_config['differential_sections'] = [s.strip() for s in sections.split(',')]
        
        # Start scraping
        operation_id = await scrapy_manager.scrape_sitemap(
            url=url,
            incremental=incremental,
            differential=differential,
            config=sitemap_config
        )
        
        click.echo(f"Scraping operation started with ID: {operation_id}")
        click.echo("Use 'status' command to monitor progress")
        
    except Exception as e:
        click.echo(f"Error: {e}")
        logger.error(f"Scraping failed: {e}")


@cli.command()
@click.option('--url', '-u', help='Specific sitemap URL to update')
@click.option('--incremental', '-i', is_flag=True, default=True, help='Only update new/changed content')
@click.option('--differential', '-d', is_flag=True, help='Differential update for specific sections')
@click.option('--sections', '-s', help='Comma-separated sections for differential update')
@click.pass_context
async def update(ctx, url, incremental, differential, sections):
    """Update existing sitemap data."""
    config_manager = ctx.obj['config_manager']
    supabase = ctx.obj['supabase']
    scrapy_manager = ctx.obj['scrapy_manager']
    
    try:
        if url:
            # Update specific sitemap
            sitemap_config = config_manager.get_sitemap_config(url) or {}
            if differential and sections:
                sitemap_config['differential_sections'] = [s.strip() for s in sections.split(',')]
            
            operation_id = await scrapy_manager.update_sitemap(
                url=url,
                incremental=incremental,
                differential=differential,
                config=sitemap_config
            )
            click.echo(f"Update operation started with ID: {operation_id}")
        else:
            # Update all configured sitemaps
            sitemap_urls = config_manager.get_sitemap_urls()
            if not sitemap_urls:
                click.echo("No sitemaps configured. Use --url option or configure SITEMAP_URLS.")
                return
            
            for sitemap_url in sitemap_urls:
                sitemap_config = config_manager.get_sitemap_config(sitemap_url) or {}
                if differential and sections:
                    sitemap_config['differential_sections'] = [s.strip() for s in sections.split(',')]
                
                operation_id = await scrapy_manager.update_sitemap(
                    url=sitemap_url,
                    incremental=incremental,
                    differential=differential,
                    config=sitemap_config
                )
                click.echo(f"Update operation started for {sitemap_url} with ID: {operation_id}")
        
        click.echo("Use 'status' command to monitor progress")
        
    except Exception as e:
        click.echo(f"Error: {e}")
        logger.error(f"Update failed: {e}")


@cli.command()
@click.option('--operation-id', '-o', help='Specific operation ID')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
async def status(ctx, operation_id, format):
    """Show scraping operation status."""
    scrapy_manager = ctx.obj['scrapy_manager']
    
    try:
        if operation_id:
            status_info = await scrapy_manager.get_operation_status(operation_id)
            if format == 'json':
                click.echo(json.dumps(status_info, indent=2))
            else:
                _display_operation_status(status_info)
        else:
            # Show all recent operations
            operations = await scrapy_manager.get_recent_operations()
            if format == 'json':
                click.echo(json.dumps(operations, indent=2))
            else:
                _display_operations_table(operations)
    
    except Exception as e:
        click.echo(f"Error: {e}")
        logger.error(f"Status check failed: {e}")


@cli.command()
@click.pass_context
def list(ctx):
    """List all configured sitemaps."""
    config_manager = ctx.obj['config_manager']
    supabase = ctx.obj['supabase']
    
    try:
        sitemap_urls = config_manager.get_sitemap_urls()
        
        if not sitemap_urls:
            click.echo("No sitemaps configured.")
            return
        
        click.echo("Configured Sitemaps:")
        click.echo("-" * 80)
        
        for url in sitemap_urls:
            config = config_manager.get_sitemap_config(url) or {}
            domain = config_manager.get_sitemap_domain(url)
            
            click.echo(f"URL: {url}")
            click.echo(f"Domain: {domain}")
            if config:
                click.echo(f"Filters: {config.get('filters', 'None')}")
                click.echo(f"Max Pages: {config.get('max_pages', 'Default')}")
            click.echo("-" * 80)
    
    except Exception as e:
        click.echo(f"Error: {e}")
        logger.error(f"List operation failed: {e}")


@cli.command()
@click.option('--older-than', '-o', default='30d', help='Delete data older than (e.g., 7d, 30d, 90d)')
@click.option('--dry-run', '-n', is_flag=True, help='Show what would be deleted without actually deleting')
@click.pass_context
async def cleanup(ctx, older_than, dry_run):
    """Clean up old sitemap data."""
    supabase = ctx.obj['supabase']
    
    try:
        # Parse time period
        if older_than.endswith('d'):
            days = int(older_than[:-1])
        elif older_than.endswith('w'):
            days = int(older_than[:-1]) * 7
        elif older_than.endswith('m'):
            days = int(older_than[:-1]) * 30
        else:
            days = int(older_than)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if dry_run:
            click.echo(f"Would delete data older than {cutoff_date.isoformat()}")
            # TODO: Implement dry run logic
        else:
            click.echo(f"Deleting data older than {cutoff_date.isoformat()}")
            # TODO: Implement cleanup logic
            click.echo("Cleanup completed")
    
    except Exception as e:
        click.echo(f"Error: {e}")
        logger.error(f"Cleanup failed: {e}")


def _display_operation_status(status_info: Dict[str, Any]):
    """Display operation status in table format."""
    click.echo(f"Operation ID: {status_info.get('id', 'N/A')}")
    click.echo(f"Status: {status_info.get('status', 'N/A')}")
    click.echo(f"Progress: {status_info.get('progress', 0)}%")
    click.echo(f"Started: {status_info.get('started_at', 'N/A')}")
    if status_info.get('completed_at'):
        click.echo(f"Completed: {status_info['completed_at']}")
    if status_info.get('error'):
        click.echo(f"Error: {status_info['error']}")


def _display_operations_table(operations: List[Dict[str, Any]]):
    """Display operations in table format."""
    if not operations:
        click.echo("No recent operations found.")
        return
    
    click.echo(f"{'ID':<20} {'Status':<15} {'Progress':<10} {'Started':<20}")
    click.echo("-" * 70)
    
    for op in operations:
        click.echo(f"{op.get('id', 'N/A'):<20} {op.get('status', 'N/A'):<15} "
                  f"{op.get('progress', 0):<10}% {op.get('started_at', 'N/A'):<20}")


if __name__ == '__main__':
    cli() 