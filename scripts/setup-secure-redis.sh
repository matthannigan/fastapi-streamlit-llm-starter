#!/bin/bash
# One-Command Secure Redis Setup Script
#
# This script provides complete secure Redis setup for development with:
# - TLS certificate generation
# - Strong password generation
# - Encryption key generation
# - Environment configuration
# - Docker container startup
# - Connection validation
#
# Usage:
#   ./scripts/setup-secure-redis.sh [--regenerate] [--production]
#
# Options:
#   --regenerate    Regenerate all certificates and keys (overwrites existing)
#   --production    Use production-grade security settings
#   --help          Show help message

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CERT_DIR="$PROJECT_ROOT/certs"
ENV_FILE="$PROJECT_ROOT/.env.secure"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.secure.yml"
DATA_DIR="$PROJECT_ROOT/data/redis"

# Default settings
REGENERATE=false
PRODUCTION=false
REDIS_HOST="redis"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${CYAN}🔐 $1${NC}"
}

# Show help
show_help() {
    cat << EOF
Secure Redis Setup Script

This script provides one-command setup for secure Redis development environment
with TLS encryption, authentication, and data encryption.

Usage:
  $0 [options]

Options:
  --regenerate     Regenerate all certificates and keys (overwrites existing)
  --production     Use production-grade security settings
  --help          Show this help message

Examples:
  $0                      # Standard secure development setup
  $0 --regenerate         # Regenerate all security materials
  $0 --production         # Production-grade security settings

What this script does:
  1. Check system dependencies (Docker, Docker Compose, OpenSSL)
  2. Generate TLS certificates for Redis server
  3. Generate strong passwords and encryption keys
  4. Create secure environment configuration
  5. Start TLS-enabled Redis container
  6. Validate secure connection
  7. Provide next steps and usage instructions

Output:
  - TLS certificates in ./certs/
  - Environment configuration in .env.secure
  - Running secure Redis container
  - Data persistence in ./data/redis/

Security Features:
  - TLS 1.2/1.3 encryption for all Redis connections
  - Strong password authentication
  - Application-layer data encryption
  - Network isolation (internal Docker networks)
  - Certificate-based validation
  - Secure file permissions
EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --regenerate)
                REGENERATE=true
                shift
                ;;
            --production)
                PRODUCTION=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Check system dependencies
check_dependencies() {
    log_info "Checking system dependencies..."

    local missing_deps=()
    local optional_deps=()

    # Check required dependencies
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("docker-compose")
    fi

    if ! command -v openssl &> /dev/null; then
        missing_deps+=("openssl")
    fi

    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi

    # Check optional but recommended dependencies
    if ! command -v redis-cli &> /dev/null; then
        optional_deps+=("redis-cli")
    fi

    # Report missing required dependencies
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        echo
        echo "Installation instructions:"
        echo
        echo "  macOS (Homebrew):"
        echo "    brew install docker docker-compose openssl python3"
        echo "    # For redis-cli: brew install redis"
        echo
        echo "  Ubuntu/Debian:"
        echo "    sudo apt-get update"
        echo "    sudo apt-get install docker.io docker-compose openssl python3 python3-pip"
        echo "    # For redis-cli: sudo apt-get install redis-tools"
        echo
        echo "  CentOS/RHEL:"
        echo "    sudo yum install docker docker-compose openssl python3"
        echo "    # For redis-cli: sudo yum install redis"
        echo
        echo "  Fedora:"
        echo "    sudo dnf install docker docker-compose openssl python3"
        echo "    # For redis-cli: sudo dnf install redis"
        echo
        exit 1
    fi

    # Check Python cryptography library
    if ! python3 -c "import cryptography" &> /dev/null; then
        log_warning "Python cryptography library not installed"
        log_info "Installing cryptography library..."
        if python3 -m pip install cryptography &> /dev/null; then
            log_success "Cryptography library installed successfully"
        else
            log_error "Failed to install cryptography library"
            echo "Install manually: python3 -m pip install cryptography"
            exit 1
        fi
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        echo
        echo "Start Docker:"
        echo "  macOS:   Start Docker Desktop application"
        echo "  Linux:   sudo systemctl start docker"
        echo "           sudo systemctl enable docker  # Start on boot"
        echo
        exit 1
    fi

    # Check Docker Compose version
    local compose_version=""
    if command -v docker-compose &> /dev/null; then
        compose_version=$(docker-compose version --short 2>/dev/null || echo "unknown")
    elif docker compose version &> /dev/null; then
        compose_version=$(docker compose version --short 2>/dev/null || echo "unknown")
    fi

    # Warn about optional dependencies
    if [ ${#optional_deps[@]} -ne 0 ]; then
        log_warning "Optional dependencies not found: ${optional_deps[*]}"
        log_info "Setup will continue, but some validation features may be limited"
    fi

    log_success "All required dependencies are available"
    log_info "Docker Compose version: $compose_version"
}

# Generate secure password
generate_secure_password() {
    local length=${1:-32}
    if command -v openssl &> /dev/null; then
        openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
    else
        # Fallback method
        < /dev/urandom tr -dc 'A-Za-z0-9!@#$%^&*-_=+' | head -c$length
    fi
}

# Generate encryption key
generate_encryption_key() {
    python3 -c "
from cryptography.fernet import Fernet
import sys
try:
    key = Fernet.generate_key()
    print(key.decode())
except ImportError:
    sys.stderr.write('Warning: cryptography library not available, using fallback\\n')
    import base64
    import os
    key = base64.urlsafe_b64encode(os.urandom(32))
    print(key.decode())
"
}

# Setup directory structure
setup_directories() {
    log_info "Setting up directory structure..."

    mkdir -p "$DATA_DIR"
    chmod 755 "$DATA_DIR"
    log_success "Data directory created: $DATA_DIR"

    cd "$PROJECT_ROOT"
}

# Generate TLS certificates
generate_certificates() {
    log_header "Generating TLS Certificates"

    if [ -d "$CERT_DIR" ] && [ "$REGENERATE" = false ]; then
        log_warning "TLS certificates already exist"
        read -p "Regenerate certificates? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Using existing certificates"
            return 0
        fi
    fi

    # Run certificate generation script
    if [ -f "$SCRIPT_DIR/init-redis-tls.sh" ]; then
        chmod +x "$SCRIPT_DIR/init-redis-tls.sh"
        "$SCRIPT_DIR/init-redis-tls.sh" "$REDIS_HOST"
    else
        log_error "Certificate generation script not found: $SCRIPT_DIR/init-redis-tls.sh"
        exit 1
    fi

    log_success "TLS certificates generated successfully"
}

# Backup existing environment file
backup_env_file() {
    if [ -f "$ENV_FILE" ]; then
        local backup_file="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Backing up existing environment file..."
        cp "$ENV_FILE" "$backup_file"
        log_success "Backup created: $backup_file"
        return 0
    fi
    return 1
}

# Preserve existing environment variables
preserve_existing_env() {
    local existing_env_file="$1"
    local preserve_vars=("NODE_ENV" "API_KEY" "CACHE_PRESET" "RESILIENCE_PRESET" "CORS_ALLOWED_ORIGINS" "LOG_LEVEL")

    if [ ! -f "$existing_env_file" ]; then
        return 1
    fi

    log_info "Preserving existing non-security environment variables..."

    # Create associative array to store preserved values
    declare -A preserved_values

    for var in "${preserve_vars[@]}"; do
        local value=$(grep "^${var}=" "$existing_env_file" | cut -d'=' -f2-)
        if [ -n "$value" ]; then
            preserved_values[$var]=$value
            log_info "  Preserving $var"
        fi
    done

    # Export preserved values for use in configuration generation
    for var in "${!preserved_values[@]}"; do
        export "PRESERVED_${var}=${preserved_values[$var]}"
    done
}

# Generate secure configuration
generate_configuration() {
    log_header "Generating Secure Configuration"

    # Check if environment file exists and handle preservation
    if [ -f "$ENV_FILE" ]; then
        log_warning "Environment file already exists: $ENV_FILE"

        if [ "$REGENERATE" = false ]; then
            read -p "Regenerate environment file? [y/N]: " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Using existing environment file"
                return 0
            fi
        fi

        # Backup and preserve existing environment
        backup_env_file
        preserve_existing_env "$ENV_FILE"
    fi

    local redis_password
    local encryption_key
    local security_level

    if [ "$PRODUCTION" = true ]; then
        redis_password=$(generate_secure_password 48)
        security_level="production"
        log_info "Using production-grade security settings"
    else
        redis_password=$(generate_secure_password 32)
        security_level="development"
        log_info "Using development security settings"
    fi

    # Generate encryption key
    log_info "Generating encryption key..."
    encryption_key=$(generate_encryption_key)

    # Create environment file with preserved values
    log_info "Creating secure environment configuration..."

    cat > "$ENV_FILE" << EOF
# Secure Redis Environment Configuration
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# Security Level: $security_level

# Redis Connection Settings
REDIS_URL=rediss://localhost:6380
REDIS_PASSWORD=$redis_password
REDIS_TLS_ENABLED=true
REDIS_TLS_CERT_PATH=$CERT_DIR/redis.crt
REDIS_TLS_KEY_PATH=$CERT_DIR/redis.key
REDIS_TLS_CA_PATH=$CERT_DIR/ca.crt
REDIS_VERIFY_CERTIFICATES=true

# Data Encryption Settings
REDIS_ENCRYPTION_KEY=$encryption_key

# Application Settings
NODE_ENV=${PRESERVED_NODE_ENV:-development}
API_KEY=${PRESERVED_API_KEY:-$(generate_secure_password 24)}

# Cache Configuration
CACHE_PRESET=${PRESERVED_CACHE_PRESET:-ai-development}
ENABLE_AI_CACHE=true

# Resilience Configuration
RESILIENCE_PRESET=${PRESERVED_RESILIENCE_PRESET:-development}

# Security Settings
CORS_ALLOWED_ORIGINS=${PRESERVED_CORS_ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:8501,http://localhost:8000}
LOG_LEVEL=${PRESERVED_LOG_LEVEL:-INFO}

# Docker Configuration
COMPOSE_PROJECT_NAME=secure_redis_stack
EOF

    chmod 600 "$ENV_FILE"
    log_success "Environment configuration created: $ENV_FILE"
}

# Start secure Redis container
start_redis_container() {
    log_header "Starting Secure Redis Container"

    # Check if containers are already running
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "redis_secure.*Up"; then
        log_warning "Redis container is already running"
        read -p "Restart containers? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Stopping existing containers..."
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
        else
            log_info "Using existing containers"
            return 0
        fi
    fi

    # Start containers
    log_info "Starting secure Redis and backend services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d redis

    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "redis_secure.*healthy"; then
            log_success "Redis container is healthy"
            break
        elif [ $attempt -eq $max_attempts ]; then
            log_error "Redis failed to start after $max_attempts attempts"
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs redis
            exit 1
        else
            log_info "Attempt $attempt/$max_attempts - waiting for Redis..."
            sleep 2
            ((attempt++))
        fi
    done
}

# Validate secure connection
validate_connection() {
    log_header "Validating Secure Connection"

    # Source environment variables
    source "$ENV_FILE"

    local validation_failed=false

    # Test 1: Certificate validity
    log_info "Validating TLS certificates..."
    if openssl x509 -in "$REDIS_TLS_CERT_PATH" -checkend 0 &> /dev/null; then
        log_success "Redis certificate is valid"

        # Check expiration warning (30 days)
        if ! openssl x509 -in "$REDIS_TLS_CERT_PATH" -checkend 2592000 &> /dev/null; then
            log_warning "Redis certificate expires within 30 days"
        fi
    else
        log_error "Redis certificate is expired or invalid"
        validation_failed=true
    fi

    # Test 2: Certificate chain verification
    log_info "Verifying certificate chain..."
    if openssl verify -CAfile "$REDIS_TLS_CA_PATH" "$REDIS_TLS_CERT_PATH" &> /dev/null; then
        log_success "Certificate chain is valid"
    else
        log_error "Certificate chain verification failed"
        validation_failed=true
    fi

    # Test 3: Container health status
    log_info "Checking Redis container health..."
    local redis_health=$(docker inspect redis_secure --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")

    if [ "$redis_health" = "healthy" ]; then
        log_success "Redis container is healthy"
    elif [ "$redis_health" = "starting" ]; then
        log_warning "Redis container is still starting up..."
        # Wait a bit longer
        sleep 5
        redis_health=$(docker inspect redis_secure --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        if [ "$redis_health" = "healthy" ]; then
            log_success "Redis container is now healthy"
        else
            log_error "Redis container health status: $redis_health"
            validation_failed=true
        fi
    else
        log_error "Redis container health status: $redis_health"
        validation_failed=true
    fi

    # Test 4: Redis TLS connection
    log_info "Testing TLS connection to Redis..."
    if command -v redis-cli &> /dev/null; then
        if redis-cli --tls \
           --cert "$REDIS_TLS_CERT_PATH" \
           --key "$REDIS_TLS_KEY_PATH" \
           --cacert "$REDIS_TLS_CA_PATH" \
           --pass "$REDIS_PASSWORD" \
           -p 6380 ping &> /dev/null; then
            log_success "Redis TLS connection successful"
        else
            log_error "Redis TLS connection failed"
            log_info "Checking Redis logs..."
            docker logs --tail 20 redis_secure 2>&1 | grep -i "error\|warning" || true
            validation_failed=true
        fi

        # Test 5: Basic Redis operations
        if [ "$validation_failed" = false ]; then
            log_info "Testing basic Redis operations..."
            local test_key="test_secure_redis_$(date +%s)"
            local test_value="test_value_$(date +%s)"

            if redis-cli --tls \
               --cert "$REDIS_TLS_CERT_PATH" \
               --key "$REDIS_TLS_KEY_PATH" \
               --cacert "$REDIS_TLS_CA_PATH" \
               --pass "$REDIS_PASSWORD" \
               -p 6380 SET "$test_key" "$test_value" &> /dev/null; then

                local retrieved_value=$(redis-cli --tls \
                   --cert "$REDIS_TLS_CERT_PATH" \
                   --key "$REDIS_TLS_KEY_PATH" \
                   --cacert "$REDIS_TLS_CA_PATH" \
                   --pass "$REDIS_PASSWORD" \
                   -p 6380 GET "$test_key" 2>/dev/null)

                if [ "$retrieved_value" = "$test_value" ]; then
                    log_success "Redis operations working correctly"
                    # Cleanup test key
                    redis-cli --tls \
                       --cert "$REDIS_TLS_CERT_PATH" \
                       --key "$REDIS_TLS_KEY_PATH" \
                       --cacert "$REDIS_TLS_CA_PATH" \
                       --pass "$REDIS_PASSWORD" \
                       -p 6380 DEL "$test_key" &> /dev/null
                else
                    log_error "Redis operations failed: value mismatch"
                    validation_failed=true
                fi
            else
                log_error "Redis operations failed: cannot SET value"
                validation_failed=true
            fi
        fi
    else
        log_warning "redis-cli not available, skipping connection and operation tests"
    fi

    # Test 6: Network isolation
    log_info "Checking network isolation..."
    local exposed_ports=$(docker port redis_secure 2>/dev/null | wc -l)
    if [ "$exposed_ports" -eq 0 ]; then
        log_success "Redis is not exposed to host (network isolated)"
    else
        log_warning "Redis has exposed ports (may not be fully isolated)"
    fi

    # Test 7: Encryption key validation
    log_info "Validating encryption key..."
    if python3 -c "
from cryptography.fernet import Fernet
import sys
try:
    key = '$REDIS_ENCRYPTION_KEY'
    Fernet(key.encode())
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
        log_success "Encryption key is valid"
    else
        log_error "Encryption key is invalid"
        validation_failed=true
    fi

    # Summary
    echo
    if [ "$validation_failed" = false ]; then
        log_success "All validation tests passed!"
    else
        log_error "Some validation tests failed - review errors above"
        log_info "Check Docker logs: docker logs redis_secure"
        return 1
    fi
}

# Show setup summary
show_setup_summary() {
    log_header "Setup Complete!"

    # Source environment to show actual values
    source "$ENV_FILE"

    echo
    echo "📋 Configuration Summary:"
    echo "   🔐 Security Level: $([ "$PRODUCTION" = true ] && echo "Production" || echo "Development")"
    echo "   🗄️  Redis URL: $REDIS_URL"
    echo "   📁 Certificates: $CERT_DIR/"
    echo "   ⚙️  Environment: $ENV_FILE"
    echo "   💾 Data Directory: $DATA_DIR"
    echo

    echo "🚀 Services Running:"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo

    echo "📖 Usage Instructions:"
    echo
    echo "   1. Load environment variables:"
    echo "      source .env.secure"
    echo
    echo "   2. Test Redis connection:"
    echo "      redis-cli --tls --cert certs/redis.crt --key certs/redis.key --cacert certs/ca.crt -p 6380 ping"
    echo
    echo "   3. Start backend application:"
    echo "      cd backend && python -m app.main"
    echo
    echo "   4. Start full stack:"
    echo "      docker-compose -f docker-compose.secure.yml --env-file .env.secure up -d"
    echo
    echo "   5. Stop services:"
    echo "      docker-compose -f docker-compose.secure.yml --env-file .env.secure down"
    echo

    echo "🔍 Monitoring & Debugging:"
    echo "   - View logs: docker-compose -f docker-compose.secure.yml logs -f redis"
    echo "   - Redis info: redis-cli --tls --cert certs/redis.crt --key certs/redis.key --cacert certs/ca.crt -p 6380 info"
    echo "   - Certificate info: openssl x509 -in certs/redis.crt -text -noout"
    echo

    echo "📚 Documentation: docs/infrastructure/redis-security.md"
    echo

    log_success "Secure Redis setup completed successfully!"
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Setup failed. Check the logs above for details."
        echo
        echo "🛠️  Troubleshooting:"
        echo "   - Ensure Docker is running"
        echo "   - Check port 6380 is not in use"
        echo "   - Verify certificates were generated correctly"
        echo "   - Review Docker logs for errors"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution function
main() {
    log_header "Secure Redis Setup Script"
    echo "========================================"
    echo

    parse_arguments "$@"
    check_dependencies
    setup_directories
    generate_certificates
    generate_configuration
    start_redis_container
    validate_connection
    show_setup_summary
}

# Run main function with all arguments
main "$@"