#!/bin/bash

set -e

BUCKET="my-data-demo-2026-20055-dr"
REGION="ap-southeast-2"
TIMESTAMP="20260921_090000"

DATABASES=(
"CSDL_A_Dancu"
"CSDL_B_Dichvucong"
"CSDL_C_Datdai"
)

echo "======================================"
echo "       DR DRILL TEST - START"
echo "======================================"

START=$(date +%s)

for db in "${DATABASES[@]}"; do

    FILE="${db}_${TIMESTAMP}.sql.gz.enc"

    echo "[DR] Downloading $db..."

    aws s3 cp \
    "s3://${BUCKET}/provincial-center/${db}/${TIMESTAMP}/${FILE}" \
    "/tmp/${FILE}" \
    --region "$REGION"

    echo "[SUCCESS] Downloaded $db"

done

END=$(date +%s)
ELAPSED=$((END-START))

echo "======================================"
echo "       DR DRILL TEST - SUCCESS"
echo "       Recovery time: ${ELAPSED}s"
echo "======================================"
