#!/bin/bash

# Health Check Script for Docker Services
# This script checks the health of all running services

set -e

echo "🏥 Health Check - FastAPI Streamlit LLM Starter"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local container_name=$2
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo -e "${GREEN}✅ ${service_name} is running${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service_name} is not running${NC}"
        return 1
    fi
}

# Function to check service health
check_health() {
    local service_name=$1
    local health_url=$2
    local container_name=$3
    
    if check_service "$service_name" "$container_name"; then
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ ${service_name} health check passed${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  ${service_name} is running but health check failed${NC}"
            return 1
        fi
    else
        return 1
    fi
}

# Function to check Redis
check_redis() {
    if check_service "Redis" "ai-text-processor-redis"; then
        if docker exec ai-text-processor-redis redis-cli ping | grep -q "PONG"; then
            echo -e "${GREEN}✅ Redis health check passed${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Redis is running but health check failed${NC}"
            return 1
        fi
    else
        return 1
    fi
}

echo "Checking Docker services..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check individual services
backend_healthy=0
frontend_healthy=0
redis_healthy=0
nginx_healthy=0

# Backend
if check_health "Backend (FastAPI)" "http://localhost:8000/health" "ai-text-processor-backend"; then
    backend_healthy=1
fi

# Frontend
if check_health "Frontend (Streamlit)" "http://localhost:8501/_stcore/health" "ai-text-processor-frontend"; then
    frontend_healthy=1
fi

# Redis
if check_redis; then
    redis_healthy=1
fi

# Nginx (optional - only in production)
if docker ps --format "table {{.Names}}" | grep -q "^ai-text-processor-nginx$"; then
    if check_service "Nginx" "ai-text-processor-nginx"; then
        nginx_healthy=1
        echo -e "${GREEN}✅ Nginx is running${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  Nginx is not running (development mode)${NC}"
    nginx_healthy=1  # Don't count as failure in dev mode
fi

echo ""
echo "📊 Service Summary:"
echo "=================="

total_services=3
healthy_services=0

if [ $backend_healthy -eq 1 ]; then
    echo -e "${GREEN}✅ Backend: Healthy${NC}"
    ((healthy_services++))
else
    echo -e "${RED}❌ Backend: Unhealthy${NC}"
fi

if [ $frontend_healthy -eq 1 ]; then
    echo -e "${GREEN}✅ Frontend: Healthy${NC}"
    ((healthy_services++))
else
    echo -e "${RED}❌ Frontend: Unhealthy${NC}"
fi

if [ $redis_healthy -eq 1 ]; then
    echo -e "${GREEN}✅ Redis: Healthy${NC}"
    ((healthy_services++))
else
    echo -e "${RED}❌ Redis: Unhealthy${NC}"
fi

echo ""
echo "📈 Overall Status: $healthy_services/$total_services services healthy"

if [ $healthy_services -eq $total_services ]; then
    echo -e "${GREEN}🎉 All services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some services are unhealthy. Check the logs for more details.${NC}"
    echo ""
    echo "Troubleshooting commands:"
    echo "  make logs           # View all logs"
    echo "  make status         # Check container status"
    echo "  make restart        # Restart all services"
    exit 1
fi 