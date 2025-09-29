#!/bin/bash
# TLS Certificate Generation Script for Secure Redis
#
# This script generates TLS certificates for Redis secure connections including:
# - Certificate Authority (CA) key and certificate
# - Redis server certificate signed by the CA
# - Proper file permissions and validation
#
# Usage:
#   ./scripts/init-redis-tls.sh [redis-hostname]
#
# Arguments:
#   redis-hostname: Optional hostname for Redis server (default: redis)
#
# Output:
#   Creates certificates in ./certs/ directory:
#   - ca.key, ca.crt: Certificate Authority files
#   - redis.key, redis.crt: Redis server certificate files

set -euo pipefail

# Configuration
CERT_DIR="./certs"
REDIS_HOST="${1:-redis}"
KEY_SIZE=4096
CERT_DAYS=365

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check dependencies
check_dependencies() {
    log_info "Checking required dependencies..."

    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL is required but not installed"
        log_info "Install with: brew install openssl (macOS) or apt-get install openssl (Ubuntu)"
        exit 1
    fi

    log_success "Dependencies check passed"
}

# Create certificate directory
setup_directory() {
    log_info "Setting up certificate directory: $CERT_DIR"

    if [ -d "$CERT_DIR" ]; then
        log_warning "Certificate directory already exists"
        read -p "Remove existing certificates? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$CERT_DIR"
            log_info "Removed existing certificate directory"
        else
            log_info "Keeping existing certificates"
            return 0
        fi
    fi

    mkdir -p "$CERT_DIR"
    cd "$CERT_DIR"
    log_success "Certificate directory created: $(pwd)"
}

# Generate Certificate Authority
generate_ca() {
    log_info "Generating Certificate Authority (CA)..."

    # Generate CA private key
    log_info "Creating CA private key ($KEY_SIZE bits)..."
    openssl genrsa -out ca.key $KEY_SIZE

    # Generate CA certificate
    log_info "Creating CA certificate (valid for $CERT_DAYS days)..."
    openssl req -x509 -new -nodes \
        -key ca.key \
        -sha256 \
        -days $CERT_DAYS \
        -out ca.crt \
        -subj "/C=US/ST=Dev/L=Development/O=Redis-CA/OU=Security/CN=Redis-CA"

    log_success "Certificate Authority generated successfully"
}

# Generate Redis server certificate
generate_redis_cert() {
    log_info "Generating Redis server certificate for host: $REDIS_HOST"

    # Generate Redis private key
    log_info "Creating Redis private key ($KEY_SIZE bits)..."
    openssl genrsa -out redis.key $KEY_SIZE

    # Generate certificate signing request
    log_info "Creating certificate signing request..."
    openssl req -new \
        -key redis.key \
        -out redis.csr \
        -subj "/C=US/ST=Dev/L=Development/O=Redis-Server/OU=Security/CN=$REDIS_HOST"

    # Create extension file for Subject Alternative Names
    cat > redis.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $REDIS_HOST
DNS.2 = localhost
DNS.3 = *.local
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # Generate Redis certificate signed by CA
    log_info "Signing Redis certificate with CA..."
    openssl x509 -req \
        -in redis.csr \
        -CA ca.crt \
        -CAkey ca.key \
        -CAcreateserial \
        -out redis.crt \
        -days $CERT_DAYS \
        -sha256 \
        -extensions v3_req \
        -extfile redis.ext

    log_success "Redis server certificate generated successfully"
}

# Set proper file permissions
set_permissions() {
    log_info "Setting secure file permissions..."

    # Private keys: readable only by owner
    chmod 600 *.key
    log_info "Private keys: read-only by owner (600)"

    # Certificates: readable by owner and group
    chmod 644 *.crt
    log_info "Certificates: readable by owner and group (644)"

    # Remove intermediate files
    if [ -f redis.csr ]; then
        rm redis.csr
        log_info "Removed certificate signing request"
    fi

    if [ -f redis.ext ]; then
        rm redis.ext
        log_info "Removed certificate extensions file"
    fi

    if [ -f ca.srl ]; then
        chmod 644 ca.srl
        log_info "CA serial file permissions set"
    fi

    log_success "File permissions configured securely"
}

# Validate generated certificates
validate_certificates() {
    log_info "Validating generated certificates..."

    # Validate CA certificate
    if openssl x509 -in ca.crt -text -noout > /dev/null 2>&1; then
        log_success "CA certificate is valid"
    else
        log_error "CA certificate validation failed"
        exit 1
    fi

    # Validate Redis certificate
    if openssl x509 -in redis.crt -text -noout > /dev/null 2>&1; then
        log_success "Redis certificate is valid"
    else
        log_error "Redis certificate validation failed"
        exit 1
    fi

    # Verify Redis certificate is signed by CA
    if openssl verify -CAfile ca.crt redis.crt > /dev/null 2>&1; then
        log_success "Redis certificate is properly signed by CA"
    else
        log_error "Redis certificate verification against CA failed"
        exit 1
    fi

    log_success "All certificates validated successfully"
}

# Display certificate information
show_certificate_info() {
    log_info "Certificate Information:"

    echo
    echo "📁 Certificate Directory: $(pwd)"
    echo "🔑 Certificate Authority:"
    echo "   - Private Key: ca.key"
    echo "   - Certificate: ca.crt"
    echo "🗄️  Redis Server ($REDIS_HOST):"
    echo "   - Private Key: redis.key"
    echo "   - Certificate: redis.crt"

    echo
    echo "📋 Certificate Details:"

    # Show CA certificate details
    echo "🔐 CA Certificate:"
    openssl x509 -in ca.crt -subject -issuer -dates -noout | sed 's/^/   /'

    echo
    # Show Redis certificate details
    echo "🗄️  Redis Certificate:"
    openssl x509 -in redis.crt -subject -issuer -dates -noout | sed 's/^/   /'

    # Show Subject Alternative Names
    echo
    echo "🌐 Subject Alternative Names:"
    openssl x509 -in redis.crt -text -noout | grep -A 10 "Subject Alternative Name" | grep -E "(DNS|IP)" | sed 's/^/   /' || echo "   None configured"
}

# Display next steps
show_next_steps() {
    echo
    log_success "TLS certificates generated successfully!"
    echo
    echo "🚀 Next Steps:"
    echo "   1. Start secure Redis:"
    echo "      docker-compose -f docker-compose.secure.yml up -d"
    echo
    echo "   2. Test TLS connection:"
    echo "      redis-cli --tls --cert redis.crt --key redis.key --cacert ca.crt -p 6380 ping"
    echo
    echo "   3. Use in application:"
    echo "      REDIS_URL=rediss://localhost:6380"
    echo "      REDIS_TLS_CERT_PATH=$(pwd)/redis.crt"
    echo "      REDIS_TLS_KEY_PATH=$(pwd)/redis.key"
    echo "      REDIS_TLS_CA_PATH=$(pwd)/ca.crt"
    echo
    echo "📚 Documentation: docs/infrastructure/redis-security.md"
}

# Main execution
main() {
    echo "🔐 Redis TLS Certificate Generation Script"
    echo "=========================================="
    echo

    check_dependencies
    setup_directory
    generate_ca
    generate_redis_cert
    set_permissions
    validate_certificates
    show_certificate_info
    show_next_steps
}

# Handle script arguments
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Redis TLS Certificate Generation Script"
    echo
    echo "Usage:"
    echo "  $0 [redis-hostname]"
    echo
    echo "Arguments:"
    echo "  redis-hostname  Hostname for Redis server (default: redis)"
    echo
    echo "Examples:"
    echo "  $0                    # Use default hostname 'redis'"
    echo "  $0 localhost          # Use 'localhost' as hostname"
    echo "  $0 redis.example.com  # Use custom hostname"
    echo
    echo "Output:"
    echo "  Creates certificates in ./certs/ directory"
    exit 0
fi

# Run main function
main "$@"