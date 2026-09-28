#!/bin/bash

set -e

echo "=========================================="
echo "     PROVINCIAL DATABASE DR DRILL"
echo "=========================================="

DATABASES=(
"CSDL_A_Dancu"
"CSDL_B_Dichvucong"
"CSDL_C_Datdai"
)

RESTORE_TIMESTAMP="${RESTORE_TIMESTAMP:-20260921_090000}"

S3_BUCKET="${S3_DR_BACKUP_BUCKET}"
DR_HOST="${DR_STANDBY_DB_HOST}"
DB_USER="${DB_USER}"

WORK_DIR="/tmp/dr_restore"

mkdir -p "$WORK_DIR"

START_TIME=$(date +%s)

echo "[ALERT] Primary Database outage simulated"
echo "[DR] Starting restore from AWS S3..."

for db in "${DATABASES[@]}"; do

    FILE="${db}_${RESTORE_TIMESTAMP}.sql.gz.enc"

    S3_KEY="provincial-center/${db}/${RESTORE_TIMESTAMP}/${FILE}"

    ENC_FILE="${WORK_DIR}/${FILE}"
    GZ_FILE="${WORK_DIR}/${db}.sql.gz"

    echo ""
    echo "[DR] Database: $db"

    echo "[S3] Downloading encrypted backup..."

    aws s3 cp \
        "s3://${S3_BUCKET}/${S3_KEY}" \
        "$ENC_FILE"

    echo "[AES-256] Decrypting..."

    openssl enc \
        -d \
        -aes-256-cbc \
        -pbkdf2 \
        -in "$ENC_FILE" \
        -out "$GZ_FILE" \
        -pass "pass:${BACKUP_ENCRYPTION_KEY}"

    echo "[DATABASE] Restoring..."

    gunzip -c "$GZ_FILE" | \
        PGPASSWORD="$DB_PASSWORD" \
        psql \
        -h "$DR_HOST" \
        -U "$DB_USER" \
        -d "$db"

    echo "[SUCCESS] $db restored"

done

END_TIME=$(date +%s)

RTO=$((END_TIME - START_TIME))

echo ""
echo "=========================================="
echo "DR RESTORE COMPLETED"
echo "RTO: ${RTO} seconds"
echo "=========================================="

if [ "$RTO" -lt 900 ]; then
    echo "[PASS] RTO < 15 minutes"
else
