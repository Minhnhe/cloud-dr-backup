#!/bin/bash

set -e

echo "=========================================="
echo "     MONGODB DISASTER RECOVERY RESTORE"
echo "=========================================="

S3_BUCKET="my-data-demo-2026-20055-dr"
AWS_REGION="ap-southeast-2"

mkdir -p restore

echo "[1/5] Tim backup moi nhat tren S3..."

BACKUP_FILE=$(aws s3api list-objects-v2 \
  --bucket "$S3_BUCKET" \
  --prefix "provincial-center/mongodb/" \
  --region "$AWS_REGION" \
  --query 'sort_by(Contents, &LastModified)[-1].Key' \
  --output text)

if [ "$BACKUP_FILE" = "None" ] || [ -z "$BACKUP_FILE" ]; then
    echo "[ERROR] Khong tim thay backup tren S3!"
    exit 1
fi

echo "[OK] Backup: $BACKUP_FILE"

echo "[2/5] Tai backup tu S3..."

aws s3 cp \
  "s3://$S3_BUCKET/$BACKUP_FILE" \
  restore/backup.archive.gz.enc \
  --region "$AWS_REGION"

echo "[OK] Download thanh cong"

echo "[3/5] Giai ma AES-256..."

openssl enc -d \
  -aes-256-cbc \
  -pbkdf2 \
  -in restore/backup.archive.gz.enc \
  -out restore/backup.archive.gz \
  -pass pass:"$BACKUP_ENCRYPTION_KEY"

echo "[OK] Giai ma thanh cong"

echo "[4/5] Giai nen backup..."

gunzip -f restore/backup.archive.gz

echo "[OK] Giai nen thanh cong"

echo "[5/5] Khoi phuc MongoDB..."

mongorestore \
  --uri="$MONGODB_URI" \
  --archive=restore/backup.archive \
  --drop

echo "[OK] Khoi phuc MongoDB thanh cong"

echo "=========================================="
echo "       DR RESTORE HOAN TAT"
echo "=========================================="