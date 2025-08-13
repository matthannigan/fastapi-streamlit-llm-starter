#!/bin/bash
# branch-dev.sh - Manage multi-branch development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default ports (increment by 10 for each branch)
declare -A BRANCH_PORTS=(
    ["main"]="8000:8501:6379"
    ["refactor/backend-tests"]="8010:8511:6389"
)

show_help() {
    echo "Branch Development Manager"
    echo "Usage: $0 <command> [branch-name]"
    echo ""
    echo "Commands:"
    echo "  start <branch>     Start development environment for branch"
    echo "  stop <branch>      Stop development environment for branch"
    echo "  status             Show status of all running environments"
    echo "  logs <branch>      Show logs for branch environment"
    echo "  clean              Stop and clean all environments"
    echo "  list               List configured branches and ports"
    echo ""
    echo "Examples:"
    echo "  $0 start main"
    echo "  $0 start feature/new-ui"
    echo "  $0 status"
}

get_current_branch() {
    git branch --show-current
}

get_branch_ports() {
    local branch="$1"
    local ports="${BRANCH_PORTS[$branch]}"
    
    if [[ -z "$ports" ]]; then
        echo "Error: Branch '$branch' not configured in BRANCH_PORTS" >&2
        echo "Available branches: ${!BRANCH_PORTS[@]}" >&2
        exit 1
    fi
    
    echo "$ports"
}

create_env_file() {
    local branch="$1"
    local ports_str=$(get_branch_ports "$branch")
    IFS=':' read -r backend_port frontend_port redis_port <<< "$ports_str"
    
    local env_file=".env.${branch//\//_}"
    
    cat > "$env_file" << EOF
# Environment for branch: $branch
BRANCH_NAME=${branch//\//_}
BACKEND_PORT=$backend_port
FRONTEND_PORT=$frontend_port
REDIS_PORT=$redis_port

# AI Configuration
GEMINI_API_KEY=${GEMINI_API_KEY}
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG
SHOW_DEBUG_INFO=true
MAX_TEXT_LENGTH=10000
EOF
    
    echo "$env_file"
}

start_branch() {
    local branch="${1:-$(get_current_branch)}"
    echo "🚀 Starting development environment for branch: $branch"
    
    # Ensure we're on the right branch
    if [[ "$(get_current_branch)" != "$branch" ]]; then
        echo "⚠️  Warning: Current branch is $(get_current_branch), but starting environment for $branch"
        echo "Consider switching to the target branch: git checkout $branch"
    fi
    
    # Create environment file
    local env_file=$(create_env_file "$branch")
    local project_name="llm-starter-${branch//\//_}"
    
    # Get ports for display
    local ports_str=$(get_branch_ports "$branch")
    IFS=':' read -r backend_port frontend_port redis_port <<< "$ports_str"
    
    echo "📋 Configuration:"
    echo "   Project: $project_name"
    echo "   Backend:  http://localhost:$backend_port"
    echo "   Frontend: http://localhost:$frontend_port"
    echo "   Redis:    localhost:$redis_port"
    echo "   Env file: $env_file"
    
    # Start services
    docker-compose \
        -f docker-compose.branch.yml \
        -p "$project_name" \
        --env-file "$env_file" \
        up -d --build
    
    echo "✅ Environment started! Access your app at:"
    echo "   🎨 Frontend: http://localhost:$frontend_port"
    echo "   🔧 Backend:  http://localhost:$backend_port"
    echo "   📊 Health:   http://localhost:$backend_port/health"
}

stop_branch() {
    local branch="${1:-$(get_current_branch)}"
    echo "🛑 Stopping development environment for branch: $branch"
    
    local project_name="llm-starter-${branch//\//_}"
    local env_file=".env.${branch//\//_}"
    
    if [[ -f "$env_file" ]]; then
        docker-compose \
            -f docker-compose.branch.yml \
            -p "$project_name" \
            --env-file "$env_file" \
            down
    else
        echo "⚠️  Environment file $env_file not found, using project name only"
        docker-compose -p "$project_name" down
    fi
    
    echo "✅ Environment stopped"
}

show_status() {
    echo "📊 Development Environment Status"
    echo "================================="
    
    for branch in "${!BRANCH_PORTS[@]}"; do
        local project_name="llm-starter-${branch//\//_}"
        local ports_str=$(get_branch_ports "$branch")
        IFS=':' read -r backend_port frontend_port redis_port <<< "$ports_str"
        
        echo ""
        echo "Branch: $branch"
        echo "  Project: $project_name"
        echo "  Ports: Backend($backend_port) Frontend($frontend_port) Redis($redis_port)"
        
        # Check if containers are running
        local running=$(docker-compose -p "$project_name" ps -q 2>/dev/null | wc -l)
        if [[ $running -gt 0 ]]; then
            echo "  Status: 🟢 RUNNING ($running containers)"
            echo "  URLs: http://localhost:$frontend_port (UI) | http://localhost:$backend_port (API)"
        else
            echo "  Status: 🔴 STOPPED"
        fi
    done
    
    echo ""
    echo "Current branch: $(get_current_branch)"
}

show_logs() {
    local branch="${1:-$(get_current_branch)}"
    local project_name="llm-starter-${branch//\//_}"
    
    echo "📋 Logs for branch: $branch"
    docker-compose -p "$project_name" logs -f
}

clean_all() {
    echo "🧹 Cleaning all development environments..."
    
    for branch in "${!BRANCH_PORTS[@]}"; do
        local project_name="llm-starter-${branch//\//_}"
        echo "  Stopping $project_name..."
        docker-compose -p "$project_name" down -v 2>/dev/null || true
    done
    
    # Clean up environment files
    rm -f .env.*_*
    
    # Clean up Docker resources
    docker system prune -f
    
    echo "✅ All environments cleaned"
}

list_branches() {
    echo "📋 Configured Branches and Ports"
    echo "================================"
    
    for branch in "${!BRANCH_PORTS[@]}"; do
        local ports_str=$(get_branch_ports "$branch")
        IFS=':' read -r backend_port frontend_port redis_port <<< "$ports_str"
        echo "  $branch"
        echo "    Backend:  $backend_port"
        echo "    Frontend: $frontend_port"
        echo "    Redis:    $redis_port"
        echo ""
    done
}

# Main command handling
case "${1:-}" in
    "start")
        start_branch "$2"
        ;;
    "stop")
        stop_branch "$2"
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "clean")
        clean_all
        ;;
    "list")
        list_branches
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac