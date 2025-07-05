#!/usr/bin/env python3
"""
Migration script to update model names in user preferences.

This script updates the ensemble_weights in existing user preferences
from the old model names to the new model names:
- "huggingface" -> "huggingface_ensemble"
- "ast" -> "ast_model"  
- "fallback" -> "fallback_classifier"
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import update, select
from app.models.user_preferences import UserPreferences
from app.core.config import settings

async def migrate_model_names():
    """Update model names in all user preferences."""
    
    # Create database engine
    database_url = settings.DATABASE_URL
    engine = create_async_engine(database_url)
    
    async with AsyncSession(engine) as session:
        # Get all user preferences that need migration
        stmt = select(UserPreferences)
        result = await session.execute(stmt)
        all_prefs = result.scalars().all()
        
        updated_count = 0
        
        for prefs in all_prefs:
            if not prefs.ensemble_weights:
                continue
                
            # Check if migration is needed
            old_weights = prefs.ensemble_weights
            needs_migration = False
            new_weights = {}
            
            # Map old names to new names
            model_mapping = {
                "huggingface": "huggingface_ensemble",
                "ast": "ast_model",
                "fallback": "fallback_classifier"
            }
            
            for old_name, weight in old_weights.items():
                if old_name in model_mapping:
                    new_name = model_mapping[old_name]
                    new_weights[new_name] = weight
                    needs_migration = True
                    print(f"Migrating {old_name} -> {new_name} (weight: {weight})")
                else:
                    # Keep existing name if it's already correct
                    new_weights[old_name] = weight
            
            if needs_migration:
                # Update the preferences
                update_stmt = (
                    update(UserPreferences)
                    .where(UserPreferences.id == prefs.id)
                    .values(ensemble_weights=new_weights)
                )
                await session.execute(update_stmt)
                updated_count += 1
                print(f"Updated preferences ID {prefs.id} (user: {prefs.anonymous_id or prefs.user_id})")
        
        if updated_count > 0:
            await session.commit()
            print(f"\n✅ Successfully migrated {updated_count} user preference records")
        else:
            print("\n✅ No migration needed - all model names are already up to date")
    
    await engine.dispose()

if __name__ == "__main__":
    print("🔧 Starting model name migration...")
    asyncio.run(migrate_model_names())
    print("🔧 Migration complete!")