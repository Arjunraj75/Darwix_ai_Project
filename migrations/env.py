from logging.config import fileConfig
from alembic import context
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



if os.getenv("DOCKER_ENV") != "true":
    os.environ['POSTGRES_HOST'] = 'localhost'
    logging.info("-> Local execution detected. POSTGRES_HOST is now 'localhost'.")
else:
    logging.info("-> Docker execution detected. Using POSTGRES_HOST from .env file.")

# Step 2: Add the project root to Python's path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Step 3: Now, import from your 'Database' package
# This will now use the correct POSTGRES_HOST value
try:
    from Database.models import Base
    from Database.connection import engine
    logging.info("-> Successfully imported 'Base' and 'engine'.")
except ImportError as e:
    logging.info(f"\n-> !!! IMPORT FAILED !!! Error: {e}")
    sys.exit(1)

if engine is None:
    logging.info("\n-> CRITICAL: Database engine is None. Migration cannot proceed.")
    logging.info("   -> Check your .env file and connection.py for errors.")
    sys.exit(1)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the imported engine."""
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline() -> None:
    raise NotImplementedError("Offline mode is not supported in this setup.")

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

print("--- Finished migrations/env.py ---")