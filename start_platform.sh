#!/usr/bin/env bash
# start_platform.sh - One-click platform launcher

echo """=================================================="""
echo "🚀 E-COMMERCE ANALYTICS PLATFORM - QUICK START"
echo """=================================================="""

# Check if Python script exists
if [ -f "scripts/deploy_platform.py" ]; then
    echo "Starting deployment..."
    echo ""
    
    # Activate virtual environment if exists
    if [ -d "venv" ]; then
        if [ "$OSTYPE" == "msys" ] || [ "$OSTYPE" == "win32" ]; then
            # Windows
            source venv/Scripts/activate
        else
            # Mac/Linux
            source venv/bin/activate
        fi
    fi
    
    # Run deployment
    python scripts/deploy_platform.py
    
else
    echo "❌ Deployment script not found!"
    echo ""
    echo "📋 Manual setup steps:" 
    echo "1. Install prerequisites: Docker, Python 3.9+, Git"
    echo "2. Clone repository: git clone <your-repo-url>"
    echo "3. Create .env file with database credentials"
    echo "4. Run: python scripts/create_schema.py"
    echo "5. Run: python scripts/run_etl.py"
    echo "6. Start Airflow: docker-compose -f docker-compose.airflow.yml up -d"
    echo "7. Start Metabase: docker-compose -f docker-compose.metabase.yml up -d"
    echo ""
    echo "💡 For detailed instructions, see README.md"
fi

echo ""
echo """=================================================="""
echo "📚 Documentation: https://github.com/yourusername/ecommerce-analytics-platform"
echo """=================================================="""
