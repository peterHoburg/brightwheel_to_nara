"""Utility to extract session cookies from browser."""
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def extract_chrome_cookies(domain: str = "mybrightwheel.com") -> Dict[str, str]:
    """
    Extract cookies from Chrome's cookie database.
    
    Args:
        domain: Domain to extract cookies for
        
    Returns:
        Dictionary of cookie name -> value pairs
    """
    cookies = {}
    
    # Chrome cookie database locations
    chrome_paths = [
        "~/Library/Application Support/Google/Chrome/Default/Cookies",  # macOS
        "~/.config/google-chrome/Default/Cookies",  # Linux
        "~/AppData/Local/Google/Chrome/User Data/Default/Cookies",  # Windows
    ]
    
    for path_str in chrome_paths:
        path = Path(path_str).expanduser()
        if path.exists():
            try:
                conn = sqlite3.connect(str(path))
                cursor = conn.cursor()
                
                # Query for cookies from the domain
                cursor.execute(
                    "SELECT name, value FROM cookies WHERE host_key LIKE ?",
                    (f"%{domain}",)
                )
                
                for name, value in cursor.fetchall():
                    cookies[name] = value
                    
                conn.close()
                logger.info(f"Extracted {len(cookies)} cookies from Chrome")
                break
                
            except Exception as e:
                logger.warning(f"Failed to read Chrome cookies: {e}")
                continue
    
    return cookies


def extract_firefox_cookies(domain: str = "mybrightwheel.com") -> Dict[str, str]:
    """
    Extract cookies from Firefox's cookie database.
    
    Args:
        domain: Domain to extract cookies for
        
    Returns:
        Dictionary of cookie name -> value pairs
    """
    cookies = {}
    
    # Firefox profile directory
    firefox_paths = [
        "~/Library/Application Support/Firefox/Profiles",  # macOS
        "~/.mozilla/firefox",  # Linux
        "~/AppData/Roaming/Mozilla/Firefox/Profiles",  # Windows
    ]
    
    for base_path_str in firefox_paths:
        base_path = Path(base_path_str).expanduser()
        if not base_path.exists():
            continue
            
        # Find profile directories
        for profile_path in base_path.glob("*.default*"):
            cookies_db = profile_path / "cookies.sqlite"
            if cookies_db.exists():
                try:
                    conn = sqlite3.connect(str(cookies_db))
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        "SELECT name, value FROM moz_cookies WHERE host LIKE ?",
                        (f"%{domain}",)
                    )
                    
                    for name, value in cursor.fetchall():
                        cookies[name] = value
                        
                    conn.close()
                    logger.info(f"Extracted {len(cookies)} cookies from Firefox")
                    break
                    
                except Exception as e:
                    logger.warning(f"Failed to read Firefox cookies: {e}")
                    continue
    
    return cookies


def get_brightwheel_v2_cookie() -> Optional[str]:
    """
    Attempt to extract the Brightwheel session cookie from browser.
    
    Returns:
        Session cookie value if found, None otherwise
    """
    # Try Chrome first
    chrome_cookies = extract_chrome_cookies()
    if "_brightwheel_v2" in chrome_cookies:
        logger.info("Found Brightwheel session cookie in Chrome")
        return chrome_cookies["_brightwheel_v2"]
    
    # Try Firefox
    firefox_cookies = extract_firefox_cookies()
    if "_brightwheel_v2" in firefox_cookies:
        logger.info("Found Brightwheel session cookie in Firefox")
        return firefox_cookies["_brightwheel_v2"]
    
    logger.warning("Could not find Brightwheel session cookie in browser")
    return None


def print_cookie_instructions():
    """Print instructions for manually extracting cookies."""
    instructions = """
To manually extract your Brightwheel session cookie:

1. Open your browser and go to https://schools.mybrightwheel.com
2. Login to your account
3. Open Developer Tools (F12 or right-click -> Inspect)
4. Go to the "Application" tab (Chrome) or "Storage" tab (Firefox)
5. Under "Cookies", find the mybrightwheel.com entry
6. Look for "_brightwheel_v2" cookie
7. Copy the cookie value (the long string)
8. Add it to your .env file:
   BRIGHTWHEEL_SESSION_COOKIE="your_cookie_value_here"

This will allow the tool to skip the interactive login process.
    """
    print(instructions)