"""SQLite database operations for lead storage."""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional

from tiktok_leads.models.lead import Lead, LeadCreate
from tiktok_leads.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for leads."""
    
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        profile_url TEXT,
        bio TEXT,
        emails TEXT,
        phones TEXT,
        followers TEXT,
        following TEXT,
        likes TEXT,
        external_link TEXT,
        verified BOOLEAN,
        scraped_at TEXT,
        source_query TEXT
    )
    """
    
    INSERT_SQL = """
    INSERT OR IGNORE INTO leads 
    (username, profile_url, bio, emails, phones, followers, following, likes, external_link, verified, scraped_at, source_query)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    SELECT_ALL_SQL = "SELECT * FROM leads"
    
    SELECT_BY_USERNAME_SQL = "SELECT * FROM leads WHERE username = ?"
    
    COUNT_SQL = "SELECT COUNT(*) FROM leads"
    
    DELETE_ALL_SQL = "DELETE FROM leads"

    def __init__(self, db_path: str):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        
    def connect(self) -> None:
        """Establish database connection."""
        try:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}") from e

    def disconnect(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            self._execute(self.CREATE_TABLE_SQL)
            logger.info("Database tables created/verified")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create tables: {e}") from e

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL statement.
        
        Args:
            sql: SQL statement
            params: SQL parameters
        
        Returns:
            Cursor object
        """
        if not self._conn:
            raise DatabaseError("Database not connected")
        
        try:
            cursor = self._conn.execute(sql, params)
            return cursor
        except sqlite3.Error as e:
            raise DatabaseError(f"SQL execution failed: {e}") from e

    def _commit(self) -> None:
        """Commit current transaction."""
        if self._conn:
            try:
                self._conn.commit()
            except sqlite3.Error as e:
                raise DatabaseError(f"Commit failed: {e}") from e

    def insert_lead(self, lead: LeadCreate) -> bool:
        """Insert a lead into the database.
        
        Args:
            lead: Lead data to insert
        
        Returns:
            True if inserted, False if duplicate
        """
        from datetime import datetime
        
        lead_data = lead.model_dump()
        lead_data["scraped_at"] = datetime.now().isoformat()
        
        values = (
            lead_data["username"],
            lead_data["profile_url"],
            lead_data["bio"],
            lead_data["emails"],
            lead_data["phones"],
            lead_data["followers"],
            lead_data["following"],
            lead_data["likes"],
            lead_data["external_link"],
            lead_data["verified"],
            lead_data["scraped_at"],
            lead_data["source_query"],
        )
        
        try:
            cursor = self._execute(self.INSERT_SQL, values)
            self._commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Inserted lead: @{lead.username}")
                return True
            else:
                logger.debug(f"Lead already exists: @{lead.username}")
                return False
        except DatabaseError as e:
            logger.error(f"Failed to insert lead @{lead.username}: {e}")
            raise

    def get_lead(self, username: str) -> Optional[Lead]:
        """Get a lead by username.
        
        Args:
            username: TikTok username
        
        Returns:
            Lead object or None if not found
        """
        try:
            cursor = self._execute(self.SELECT_BY_USERNAME_SQL, (username,))
            row = cursor.fetchone()
            
            if row:
                return Lead(
                    id=row["id"],
                    username=row["username"],
                    profile_url=row["profile_url"],
                    bio=row["bio"],
                    emails=row["emails"],
                    phones=row["phones"],
                    followers=row["followers"],
                    following=row["following"],
                    likes=row["likes"],
                    external_link=row["external_link"],
                    verified=row["verified"],
                    scraped_at=row["scraped_at"],
                    source_query=row["source_query"],
                )
            return None
        except DatabaseError as e:
            logger.error(f"Failed to get lead @{username}: {e}")
            raise

    def get_all_leads(self) -> List[Lead]:
        """Get all leads from the database.
        
        Returns:
            List of Lead objects
        """
        try:
            cursor = self._execute(self.SELECT_ALL_SQL)
            rows = cursor.fetchall()
            
            leads = []
            for row in rows:
                leads.append(Lead(
                    id=row["id"],
                    username=row["username"],
                    profile_url=row["profile_url"],
                    bio=row["bio"],
                    emails=row["emails"],
                    phones=row["phones"],
                    followers=row["followers"],
                    following=row["following"],
                    likes=row["likes"],
                    external_link=row["external_link"],
                    verified=row["verified"],
                    scraped_at=row["scraped_at"],
                    source_query=row["source_query"],
                ))
            
            logger.info(f"Retrieved {len(leads)} leads from database")
            return leads
        except DatabaseError as e:
            logger.error(f"Failed to get all leads: {e}")
            raise

    def count_leads(self) -> int:
        """Count total leads in database.
        
        Returns:
            Number of leads
        """
        try:
            cursor = self._execute(self.COUNT_SQL)
            result = cursor.fetchone()
            return result[0] if result else 0
        except DatabaseError as e:
            logger.error(f"Failed to count leads: {e}")
            raise

    def clear_all(self) -> None:
        """Clear all leads from database."""
        try:
            self._execute(self.DELETE_ALL_SQL)
            self._commit()
            logger.info("All leads cleared from database")
        except DatabaseError as e:
            logger.error(f"Failed to clear leads: {e}")
            raise
