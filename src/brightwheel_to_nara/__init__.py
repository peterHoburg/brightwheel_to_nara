"""Brightwheel to Nara data transfer tool."""
import asyncio
import sys
import logging
from typing import Optional
import argparse

from .transfer import main as transfer_main
from .config import get_settings
from .utils.cookie_extractor import get_brightwheel_v2_cookie, print_cookie_instructions


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Transfer data from Brightwheel to Nara Baby Tracker"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no data will be written to Nara)"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="Number of days to sync backward from today (default: 7)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    parser.add_argument(
        "--extract-cookie",
        action="store_true",
        help="Attempt to extract session cookie from browser and show instructions"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle cookie extraction
    if args.extract_cookie:
        cookie = get_brightwheel_v2_cookie()
        if cookie:
            print(f"Found session cookie: {cookie[:20]}...")
            print(f"Add this to your .env file:")
            print(f'BRIGHTWHEEL_SESSION_COOKIE="{cookie}"')
        else:
            print_cookie_instructions()
        return
    
    # Override settings from command line
    settings = get_settings()
    if args.dry_run:
        settings.dry_run = True
    if args.days_back:
        settings.sync_days_back = args.days_back
        
    logger = logging.getLogger(__name__)
    
    try:
        # Print banner
        print("=" * 60)
        print("Brightwheel to Nara Transfer Tool")
        print("=" * 60)
        
        if settings.dry_run:
            print("🔍 Running in DRY RUN mode - no data will be written")
        print(f"📅 Syncing {settings.sync_days_back} days of data")
        print()
        
        # Run the transfer
        asyncio.run(transfer_main())
        
    except KeyboardInterrupt:
        logger.info("Transfer interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        sys.exit(1)
