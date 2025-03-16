# core/sessions.py
from django.contrib.sessions.backends.db import SessionStore as DefaultSessionStore
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
import logging

logger = logging.getLogger(__name__)

class TabSpecificSessionStore(DefaultSessionStore):
    def __init__(self, session_key=None, tab_id=None):
        self.tab_id = tab_id or 'default'
        logger.info(f"Initializing TabSpecificSessionStore with tab_id: {self.tab_id}, session_key: {session_key}")
        # Prefix the session key with tab_id to isolate sessions per tab
        if session_key:
            prefixed_key = f"{self.tab_id}:{session_key}"
            super().__init__(prefixed_key)
        else:
            super().__init__(session_key)

    def load(self):
        logger.info(f"Loading session for tab {self.tab_id}, session_key: {self._session_key}")
        try:
            return super().load()
        except (EOFError, SuspiciousOperation) as e:
            logger.error(f"Error loading session for tab {self.tab_id}: {str(e)}", exc_info=True)
            self.create()
            return {}

    def create(self):
        logger.info(f"Creating new session for tab {self.tab_id}")
        try:
            # Generate a new session key and prefix it with tab_id
            self._session_key = self._get_new_session_key()
            prefixed_key = f"{self.tab_id}:{self._session_key}"
            self._session_key = prefixed_key
            # Let the parent class handle the actual creation
            super().create()
            self.modified = True
            logger.info(f"Created session for tab {self.tab_id}, session_key: {self._session_key}")
            return {}
        except Exception as e:
            logger.error(f"Error creating session for tab {self.tab_id}: {str(e)}", exc_info=True)
            raise

    def save(self, must_create=False):
        logger.info(f"Saving session for tab {self.tab_id}, session_key: {self._session_key}, must_create: {must_create}")
        try:
            super().save(must_create)
            self.modified = False
            logger.info(f"Saved session for tab {self.tab_id}")
        except Exception as e:
            logger.error(f"Error saving session for tab {self.tab_id}: {str(e)}", exc_info=True)
            raise

    def exists(self, session_key):
        logger.info(f"Checking if session exists for tab {self.tab_id}, session_key: {session_key}")
        return super().exists(session_key)

    @classmethod
    def clear_expired(cls):
        logger.info("Clearing expired sessions")
        super().clear_expired()