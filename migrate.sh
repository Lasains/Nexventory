#!/bin/bash

# Migration helper script for Nexventory
# Usage: ./migrate.sh [message]

echo "🔄 Database Migration Helper"
echo "============================"

# Activate virtual environment
source venv/bin/activate

# Check if message is provided
MESSAGE=${1:-"Auto migration"}

echo "📝 Creating migration: $MESSAGE"

# Create migration
flask db migrate -m "$MESSAGE"

if [ $? -eq 0 ]; then
    echo "✅ Migration created successfully!"
    
    echo "🔄 Applying migration..."
    
    # Apply migration
    flask db upgrade
    
    if [ $? -eq 0 ]; then
        echo "✅ Migration applied successfully!"
        echo "🎉 Database is now up to date!"
    else
        echo "❌ Failed to apply migration"
        exit 1
    fi
else
    echo "❌ Failed to create migration"
    exit 1
fi
