#!/usr/bin/env python3
"""Automatic migration script for model changes"""

import os
import sys
import subprocess
from flask import Flask
from flask_migrate import migrate, upgrade
from app import create_app

def auto_migrate():
    """Automatically detect and apply model changes"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking for model changes...")
            
            # Create migration if there are changes
            result = subprocess.run([
                'flask', 'db', 'migrate', '-m', 'Auto migration'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("📝 Migration created successfully!")
                
                # Apply the migration
                upgrade_result = subprocess.run([
                    'flask', 'db', 'upgrade'
                ], capture_output=True, text=True)
                
                if upgrade_result.returncode == 0:
                    print("✅ Migration applied successfully!")
                    print("🔄 Database updated with latest changes!")
                else:
                    print("❌ Error applying migration:")
                    print(upgrade_result.stderr)
            else:
                if "No changes in schema detected" in result.stdout:
                    print("✅ No schema changes detected - database is up to date!")
                else:
                    print("❌ Error creating migration:")
                    print(result.stderr)
                    
        except Exception as e:
            print(f"❌ Error during auto-migration: {e}")

if __name__ == "__main__":
    auto_migrate()
