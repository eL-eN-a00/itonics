# To centralize SQL calls (with psycog2?) and check permissions (user_space_permissions table)

import os
import psycopg2
import time
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self) -> None:
        """Initializes the database manager and loads configuration."""
        # These env vars should be provided by the docker-compose postgres service
        self.dbname= os.getenv("POSTGRES_DB", "technical_assessment")
        self.user= os.getenv("POSTGRES_USER", "postgres")
        self.password= os.getenv("POSTGRES_PASSWORD", "postgres")
        self.host= os.getenv("POSTGRES_HOST", "postgres")
        self.port= os.getenv("POSTGRES_PORT", "5432")

    def _get_connection(self) -> Any:
        """Get connection to the SQL Database"""
        return psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )
    
    # Security first : the check_permission method ensures we aren't just building a "cool AI"
    # it is a "secure enterprise tool"
    def check_permission(self, user_uri: str, space_uri: str, verb: str) -> bool:
        """
        CRITICAL: Validates if a user has the right to perform an action.
        Verbs: 'read', 'write', 'delete' (from permission_verbs table)
        """
        query = """
            SELECT 1
            FROM user_space_permissions usp
            JOIN permission_verbs pv ON usp.verb_uri = pv.uri
            WHERE usp.user_uri = %s
                AND usp.space_uri = %s
                AND pv.name = %s
            """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_uri, space_uri, verb))
                return cur.fetchone() is not None
    
    # when building the Elements Agent later, i won't have to write a single line of SQL.
    # I'll just have to call db.search_elements()
    def search_elements(self, space_uri: str, search_query: str) -> List[Dict[str, Any]]:
        """Finds elements by title within a specific space."""
        query = """
            SELECT uri, title, type_uri, creation_date
            FROM elements
            WHERE space_uri = %s AND title ILIKE %s
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (space_uri, f"%{search_query}%"))
                return list(cur.fetchall())
    
    def update_element_title(self, element_uri: str, new_title : str) -> bool:
        """Updates the title of an existing element."""
        query = "UPDATE elements SET title = %s WHERE uri = %s"
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (element_uri, new_title))
                conn.commit()
                return cur.rowcount > 0
    
    def create_element(self, uri: str, title: str, type_uri: str, space_uri: str, author_uri: str) -> None:
        """Inserts a new element."""
        query = """
            INSERT INTO elements (uri, title, type_uri, space_uri, author, creation_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (uri, title, type_uri, space_uri, author_uri, int(time.time())))
                conn.commit()
