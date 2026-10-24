#!/usr/bin/env bash
# scripts/launch_metabase.sh

echo "🚀 Launching Metabase for E-commerce Analytics..."
echo """=================================================="""

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if Metabase is already running
if docker ps | grep -q "metabase"; then
    echo "⚠️  Metabase is already running."
else
    echo "📦 Starting Metabase containers..."
    docker-compose -f docker-compose.metabase.yml up -d
    
    echo "⏳ Waiting for Metabase to initialize (30 seconds)..."
    sleep 30
fi

# Run setup script
echo "🔧 Running setup script..."
python scripts/setup_metabase.py

echo ""
echo """=================================================="""
echo "🎉 METABASE IS READY!"
echo """=================================================="""
echo ""
echo "📊 Access your dashboard at: http://localhost:3000"
echo ""
echo "🔑 Login credentials:"
echo "   Email: admin@ecommerce.com"
echo "   Password: SET_METABASE_ADMIN_PASSWORD_IN_ENV"
echo ""
echo "📋 Available features:"
echo "   • Interactive dashboards"
echo "   • SQL query editor"
echo "   • Automated reports"
echo "   • Data alerts"
echo ""
echo "🛑 To stop Metabase: docker-compose -f docker-compose.metabase.yml down"
