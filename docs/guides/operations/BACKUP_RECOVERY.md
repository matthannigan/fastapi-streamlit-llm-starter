---
sidebar_label: Backup & Recovery
---

# Backup & Recovery Guide

This guide provides comprehensive backup and recovery procedures for the FastAPI-Streamlit-LLM Starter Template. It covers data backup strategies, configuration preservation, and disaster recovery workflows.

## Overview

The backup and recovery strategy focuses on preserving critical application data, configurations, and operational state to ensure rapid service restoration in case of failures or data loss.

## Backup Strategy

### Critical Data Components

| Component | Backup Frequency | Retention | Priority |
|-----------|------------------|-----------|----------|
| **Application Configuration** | Daily | 30 days | Critical |
| **Redis Cache Data** | Hourly | 7 days | High |
| **Resilience Configuration** | On change | 90 days | Critical |
| **Monitoring Metrics** | Daily | 30 days | Medium |
| **Security Configuration** | On change | 90 days | Critical |
| **Application Logs** | Daily | 14 days | Medium |

### Backup Locations

**Local Backups:**
- `/backups/daily/` - Daily automated backups
- `/backups/hourly/` - Hourly cache snapshots
- `/backups/config/` - Configuration backups

**Remote Backups:**
- Cloud storage (S3, GCS, Azure Blob)
- Network-attached storage (NAS)
- Remote backup service

## Configuration Backup

### Application Configuration

#### Daily Configuration Backup

**Automated Configuration Backup:**
```bash
#!/bin/bash
# backup_config.sh - Daily configuration backup

BACKUP_DIR="/backups/config/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "Starting configuration backup $(date)"

# 1. Export resilience configuration
echo "Backing up resilience configuration..."
curl -s http://localhost:8000/internal/resilience/config/export > "$BACKUP_DIR/resilience_config.json"

# 2. Export cache configuration
echo "Backing up cache configuration..."
curl -s http://localhost:8000/internal/cache/config/export > "$BACKUP_DIR/cache_config.json"

# 3. Export monitoring configuration
echo "Backing up monitoring configuration..."
curl -s http://localhost:8000/internal/monitoring/config/export > "$BACKUP_DIR/monitoring_config.json"

# 4. Export security configuration
echo "Backing up security configuration..."
curl -s http://localhost:8000/internal/security/config/export > "$BACKUP_DIR/security_config.json"

# 5. Backup environment configuration
echo "Backing up environment configuration..."
cp .env "$BACKUP_DIR/environment.env" 2>/dev/null || echo "No .env file found"

# 6. Backup Docker configuration
echo "Backing up Docker configuration..."
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml"
cp Dockerfile* "$BACKUP_DIR/" 2>/dev/null || echo "No Dockerfiles found"

# 7. Create backup manifest
cat > "$BACKUP_DIR/backup_manifest.json" << EOF
{
  "backup_timestamp": "$(date -Iseconds)",
  "backup_type": "configuration",
  "files": [
    "resilience_config.json",
    "cache_config.json", 
    "monitoring_config.json",
    "security_config.json",
    "environment.env",
    "docker-compose.yml"
  ],
  "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "backup_size_bytes": $(du -sb "$BACKUP_DIR" | cut -f1)
}
EOF

# 8. Compress backup
tar -czf "$BACKUP_DIR.tar.gz" -C "$BACKUP_DIR" .
rm -rf "$BACKUP_DIR"

echo "Configuration backup completed: $BACKUP_DIR.tar.gz"
```

#### Manual Configuration Export

**Export Current Configuration:**
```bash
# Create manual configuration export
mkdir -p manual_backup_$(date +%Y%m%d_%H%M%S)
cd manual_backup_$(date +%Y%m%d_%H%M%S)

# Export all configuration
curl -s http://localhost:8000/internal/resilience/config/export > resilience_config.json
curl -s http://localhost:8000/internal/cache/config/export > cache_config.json
curl -s http://localhost:8000/internal/monitoring/config/export > monitoring_config.json

# Verify exports
echo "Configuration exports:"
ls -la *.json
```

### Environment Configuration

**Environment Backup:**
```bash
# Backup environment variables
env | grep -E "(API_KEY|REDIS|GEMINI|RESILIENCE)" > environment_backup.env

# Backup with encryption (recommended for production)
env | grep -E "(API_KEY|REDIS|GEMINI|RESILIENCE)" | gpg --cipher-algo AES256 --compress-algo 1 --symmetric --output environment_backup.env.gpg
```

## Data Backup

### Redis Cache Backup

#### Automated Redis Backup

**Hourly Redis Backup:**
```bash
#!/bin/bash
# backup_redis.sh - Hourly Redis cache backup

BACKUP_DIR="/backups/redis/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

echo "Starting Redis backup $(date)"

# 1. Create Redis snapshot
redis-cli bgsave

# 2. Wait for background save to complete
while [ "$(redis-cli lastsave)" = "$(redis-cli lastsave)" ]; do
    sleep 1
done

# 3. Copy RDB file
cp /var/lib/redis/dump.rdb "$BACKUP_FILE"

# 4. Export cache statistics
curl -s http://localhost:8000/internal/cache/stats > "$BACKUP_DIR/cache_stats_$TIMESTAMP.json"

# 5. Create backup metadata
cat > "$BACKUP_DIR/redis_backup_$TIMESTAMP.meta" << EOF
{
  "backup_timestamp": "$(date -Iseconds)",
  "backup_type": "redis_cache",
  "backup_file": "redis_backup_$TIMESTAMP.rdb",
  "redis_info": $(redis-cli info server | grep -E "redis_version|used_memory" | jq -Rs 'split("\n") | map(select(length > 0)) | map(split(":")) | from_entries'),
  "backup_size_bytes": $(stat -c%s "$BACKUP_FILE")
}
EOF

# 6. Compress backup
gzip "$BACKUP_FILE"

echo "Redis backup completed: $BACKUP_FILE.gz"

# 7. Cleanup old backups (keep 7 days)
find /backups/redis -name "*.gz" -mtime +7 -delete
find /backups/redis -name "*.meta" -mtime +7 -delete
```

#### Manual Redis Backup

**Manual Cache Export:**
```bash
# Export cache data via API
curl -s http://localhost:8000/internal/cache/export > cache_export_$(date +%Y%m%d_%H%M%S).json

# Or direct Redis backup
redis-cli bgsave
cp /var/lib/redis/dump.rdb redis_manual_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Monitoring Data Backup

#### Metrics and Logs Backup

**Daily Monitoring Backup:**
```bash
#!/bin/bash
# backup_monitoring.sh - Daily monitoring data backup

BACKUP_DIR="/backups/monitoring/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "Starting monitoring data backup $(date)"

# 1. Export monitoring metrics
curl -s "http://localhost:8000/internal/monitoring/metrics?time_window_hours=24" > "$BACKUP_DIR/monitoring_metrics.json"

# 2. Export performance data
curl -s http://localhost:8000/internal/monitoring/performance-history > "$BACKUP_DIR/performance_history.json"

# 3. Export alert history
curl -s http://localhost:8000/internal/monitoring/alerts/history > "$BACKUP_DIR/alert_history.json"

# 4. Backup application logs
cp backend/logs/*.log "$BACKUP_DIR/" 2>/dev/null || echo "No log files found"

# 5. Backup resilience metrics
curl -s http://localhost:8000/internal/resilience/metrics/export > "$BACKUP_DIR/resilience_metrics.json"

# 6. Create monitoring backup manifest
cat > "$BACKUP_DIR/monitoring_manifest.json" << EOF
{
  "backup_timestamp": "$(date -Iseconds)",
  "backup_type": "monitoring_data",
  "time_window_hours": 24,
  "files": $(ls "$BACKUP_DIR"/*.json | jq -R . | jq -s .),
  "total_size_bytes": $(du -sb "$BACKUP_DIR" | cut -f1)
}
EOF

echo "Monitoring backup completed"
```

## Recovery Procedures

### Configuration Recovery

#### Complete Configuration Restore

**Restore from Backup:**
```bash
#!/bin/bash
# restore_config.sh - Restore configuration from backup

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

RESTORE_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESTORE_DIR"

echo "Starting configuration restore from $BACKUP_FILE"

# 1. Extract backup
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# 2. Verify backup integrity
if [ ! -f "$RESTORE_DIR/backup_manifest.json" ]; then
    echo "Error: Invalid backup file - no manifest found"
    exit 1
fi

# 3. Restore resilience configuration
if [ -f "$RESTORE_DIR/resilience_config.json" ]; then
    echo "Restoring resilience configuration..."
    curl -X POST http://localhost:8000/internal/resilience/config/import \
      -H "Content-Type: application/json" \
      -d @"$RESTORE_DIR/resilience_config.json"
fi

# 4. Restore cache configuration
if [ -f "$RESTORE_DIR/cache_config.json" ]; then
    echo "Restoring cache configuration..."
    curl -X POST http://localhost:8000/internal/cache/config/import \
      -H "Content-Type: application/json" \
      -d @"$RESTORE_DIR/cache_config.json"
fi

# 5. Restore monitoring configuration
if [ -f "$RESTORE_DIR/monitoring_config.json" ]; then
    echo "Restoring monitoring configuration..."
    curl -X POST http://localhost:8000/internal/monitoring/config/import \
      -H "Content-Type: application/json" \
      -d @"$RESTORE_DIR/monitoring_config.json"
fi

# 6. Restore environment configuration
if [ -f "$RESTORE_DIR/environment.env" ]; then
    echo "Restoring environment configuration..."
    cp "$RESTORE_DIR/environment.env" .env
    echo "Warning: Restart required for environment changes"
fi

# 7. Verify restoration
echo "Verifying configuration restoration..."
curl -s http://localhost:8000/internal/monitoring/health | jq '.status'

echo "Configuration restore completed"
rm -rf "$RESTORE_DIR"
```

#### Selective Configuration Restore

**Restore Specific Components:**
```bash
# Restore only resilience configuration
curl -X POST http://localhost:8000/internal/resilience/config/import \
  -H "Content-Type: application/json" \
  -d @resilience_config_backup.json

# Restore only cache configuration
curl -X POST http://localhost:8000/internal/cache/config/import \
  -H "Content-Type: application/json" \
  -d @cache_config_backup.json

# Verify specific restoration
curl -s http://localhost:8000/internal/resilience/health | jq '.'
curl -s http://localhost:8000/internal/cache/stats | jq '.'
```

### Redis Data Recovery

#### Redis Restore from Backup

**Complete Redis Restore:**
```bash
#!/bin/bash
# restore_redis.sh - Restore Redis from backup

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <redis_backup.rdb.gz>"
    exit 1
fi

echo "Starting Redis restore from $BACKUP_FILE"

# 1. Stop Redis service
redis-cli shutdown nosave

# 2. Backup current data
cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null

# 3. Restore from backup
gunzip -c "$BACKUP_FILE" > /var/lib/redis/dump.rdb

# 4. Set proper permissions
chown redis:redis /var/lib/redis/dump.rdb
chmod 660 /var/lib/redis/dump.rdb

# 5. Start Redis service
redis-server /etc/redis/redis.conf &

# 6. Wait for Redis to start
sleep 5

# 7. Verify restoration
redis-cli ping
if [ $? -eq 0 ]; then
    echo "Redis restore completed successfully"
    redis-cli info keyspace
else
    echo "Redis restore failed"
    exit 1
fi
```

#### Cache Data Import

**Import Cache Data via API:**
```bash
# Import cache data from JSON export
curl -X POST http://localhost:8000/internal/cache/import \
  -H "Content-Type: application/json" \
  -d @cache_export_backup.json

# Verify cache import
curl -s http://localhost:8000/internal/cache/stats | jq '.entry_count'
```

### Application Recovery

#### Complete Application Restore

**Full Application Recovery:**
```bash
#!/bin/bash
# restore_application.sh - Complete application recovery

CONFIG_BACKUP="$1"
REDIS_BACKUP="$2"

if [ -z "$CONFIG_BACKUP" ] || [ -z "$REDIS_BACKUP" ]; then
    echo "Usage: $0 <config_backup.tar.gz> <redis_backup.rdb.gz>"
    exit 1
fi

echo "Starting complete application recovery $(date)"

# 1. Stop all services
docker-compose down

# 2. Restore configuration
./restore_config.sh "$CONFIG_BACKUP"

# 3. Restore Redis data
./restore_redis.sh "$REDIS_BACKUP"

# 4. Start services
docker-compose up -d

# 5. Wait for services to be ready
sleep 30

# 6. Verify application health
echo "Verifying application health..."
curl -f http://localhost:8000/health
curl -f http://localhost:8501/

# 7. Run post-recovery checks
curl -s http://localhost:8000/internal/monitoring/health | jq '.'
curl -s http://localhost:8000/internal/cache/stats | jq '.health'

echo "Application recovery completed $(date)"
```

## Disaster Recovery

### Recovery Time Objectives (RTO)

| Component | RTO Target | Maximum RTO | Dependencies |
|-----------|------------|-------------|--------------|
| **Configuration** | < 15 minutes | 30 minutes | Backup availability |
| **Cache Data** | < 30 minutes | 1 hour | Redis backup |
| **Complete Application** | < 1 hour | 2 hours | All backups |
| **Monitoring Data** | < 2 hours | 4 hours | Backup availability |

### Recovery Point Objectives (RPO)

| Data Type | RPO Target | Backup Frequency | Max Data Loss |
|-----------|------------|------------------|---------------|
| **Configuration** | < 1 hour | On change | Latest changes |
| **Cache Data** | < 1 hour | Hourly | 1 hour of cache |
| **Monitoring Metrics** | < 24 hours | Daily | 1 day of metrics |
| **Application Logs** | < 24 hours | Daily | 1 day of logs |

### Disaster Recovery Workflow

#### DR Activation Checklist

**Phase 1: Assessment (< 10 minutes)**
- [ ] Identify scope of disaster
- [ ] Assess data loss extent
- [ ] Verify backup availability
- [ ] Determine recovery strategy

**Phase 2: Recovery (< 1 hour)**
- [ ] Provision new infrastructure if needed
- [ ] Restore application configuration
- [ ] Restore Redis data
- [ ] Start application services
- [ ] Verify basic functionality

**Phase 3: Validation (< 30 minutes)**
- [ ] Run health checks
- [ ] Verify API functionality
- [ ] Test critical workflows
- [ ] Monitor system performance

**Phase 4: Notification (< 15 minutes)**
- [ ] Notify stakeholders
- [ ] Update status pages
- [ ] Document recovery actions
- [ ] Schedule post-incident review

### DR Testing

#### Monthly DR Test

**DR Test Procedure:**
```bash
#!/bin/bash
# dr_test.sh - Monthly disaster recovery test

TEST_ENV="dr_test_$(date +%Y%m%d)"
mkdir -p "/tmp/$TEST_ENV"

echo "Starting DR test $(date)"

# 1. Create test backups
./backup_config.sh
./backup_redis.sh

# 2. Simulate disaster (stop services)
docker-compose down
docker volume rm $(docker volume ls -q)

# 3. Perform recovery
LATEST_CONFIG=$(ls -t /backups/config/*.tar.gz | head -1)
LATEST_REDIS=$(ls -t /backups/redis/*.rdb.gz | head -1)

./restore_application.sh "$LATEST_CONFIG" "$LATEST_REDIS"

# 4. Verify recovery
echo "Verifying DR test..."
curl -f http://localhost:8000/health
curl -f http://localhost:8501/

# 5. Document test results
cat > "/tmp/$TEST_ENV/dr_test_results.json" << EOF
{
  "test_timestamp": "$(date -Iseconds)",
  "recovery_time_minutes": $((($(date +%s) - $START_TIME) / 60)),
  "config_backup_used": "$LATEST_CONFIG",
  "redis_backup_used": "$LATEST_REDIS",
  "health_check_passed": $(curl -s http://localhost:8000/health >/dev/null && echo true || echo false),
  "services_restored": {
    "backend": $(curl -s http://localhost:8000/health >/dev/null && echo true || echo false),
    "frontend": $(curl -s http://localhost:8501/ >/dev/null && echo true || echo false)
  }
}
EOF

echo "DR test completed"
```

## Backup Monitoring

### Backup Health Monitoring

**Daily Backup Verification:**
```bash
#!/bin/bash
# verify_backups.sh - Daily backup verification

echo "Verifying backup health $(date)"

# 1. Check configuration backups
CONFIG_BACKUP_COUNT=$(find /backups/config -name "*.tar.gz" -mtime -1 | wc -l)
if [ $CONFIG_BACKUP_COUNT -eq 0 ]; then
    echo "ERROR: No recent configuration backups found"
fi

# 2. Check Redis backups
REDIS_BACKUP_COUNT=$(find /backups/redis -name "*.gz" -mtime -1 | wc -l)
if [ $REDIS_BACKUP_COUNT -eq 0 ]; then
    echo "ERROR: No recent Redis backups found"
fi

# 3. Verify backup integrity
LATEST_CONFIG=$(ls -t /backups/config/*.tar.gz | head -1)
if [ -n "$LATEST_CONFIG" ]; then
    tar -tzf "$LATEST_CONFIG" >/dev/null || echo "ERROR: Corrupted config backup: $LATEST_CONFIG"
fi

# 4. Check backup sizes
find /backups -name "*.gz" -size -1k -exec echo "WARNING: Small backup file: {}" \;

# 5. Monitor storage usage
BACKUP_SIZE=$(du -sh /backups | cut -f1)
echo "Total backup storage usage: $BACKUP_SIZE"

echo "Backup verification completed"
```

### Automated Backup Monitoring

**Backup Alert System:**
```bash
# Add to crontab for automated monitoring
# 0 6 * * * /path/to/verify_backups.sh | mail -s "Daily Backup Report" admin@company.com

# Monitor backup job status
curl -s http://localhost:8000/internal/monitoring/backup-status | jq '.'
```

## Best Practices

### Backup Strategy

1. **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite
2. **Regular Testing**: Test restore procedures monthly
3. **Automation**: Automate backup processes
4. **Verification**: Verify backup integrity regularly
5. **Documentation**: Document all backup and recovery procedures

### Security Considerations

1. **Encryption**: Encrypt sensitive backup data
2. **Access Control**: Restrict backup access to authorized personnel
3. **Secure Storage**: Use secure backup storage locations
4. **Key Management**: Securely manage encryption keys
5. **Audit Trail**: Maintain backup access audit logs

### Recovery Planning

1. **Clear Procedures**: Document step-by-step recovery procedures
2. **Regular Training**: Train staff on recovery procedures
3. **Test Environments**: Use test environments for recovery testing
4. **Communication Plan**: Establish disaster communication procedures
5. **Continuous Improvement**: Regular review and improvement of DR plans

## Related Documentation

- **[Monitoring Guide](./MONITORING.md)**: System monitoring for backup verification
- **[Troubleshooting Guide](./TROUBLESHOOTING.md)**: Recovery troubleshooting procedures
- **[Security Guide](../SECURITY.md)**: Security considerations for backups
- **[Deployment Guide](../DEPLOYMENT.md)**: Deployment considerations for backup systems
- **[Infrastructure Documentation](../infrastructure/)**: Technical service architecture