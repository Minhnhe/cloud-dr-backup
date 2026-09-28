import os
import subprocess
import gzip
import shutil
from datetime import datetime
import boto3

print("=" * 50)
print("MONGODB DISASTER RECOVERY BACKUP")
print("=" * 50)

# =========================
# CONFIGURATION
# =========================

MONGODB_URI = os.getenv("MONGODB_URI")
S3_BUCKET = os.getenv("S3_BUCKET", "my-data-demo-2026-20055-dr")
AWS_REGION = "ap-southeast-2"
ENCRYPTION_KEY = os.getenv("BACKUP_ENCRYPTION_KEY")

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP_DIR = "backup"
os.makedirs(BACKUP_DIR, exist_ok=True)

ARCHIVE_FILE = f"{BACKUP_DIR}/cloud_dr_{TIMESTAMP}.archive"
GZIP_FILE = f"{ARCHIVE_FILE}.gz"
ENCRYPTED_FILE = f"{GZIP_FILE}.enc"

# =========================
# CHECK CONFIG
# =========================

if not MONGODB_URI:
    raise Exception("MONGODB_URI chưa được cấu hình")

if not ENCRYPTION_KEY:
    raise Exception("BACKUP_ENCRYPTION_KEY chưa được cấu hình")

print(f"[INFO] S3 Bucket: {S3_BUCKET}")
print(f"[INFO] AWS Region: {AWS_REGION}")

# =========================
# 1. MONGODB BACKUP
# =========================

print("[1/4] Dang backup MongoDB...")

subprocess.run([
    "mongodump",
    "--uri", MONGODB_URI,
    "--archive=" + ARCHIVE_FILE
], check=True)

print("[OK] MongoDB backup thanh cong")

# =========================
# 2. GZIP
# =========================

print("[2/4] Dang nen backup...")

with open(ARCHIVE_FILE, "rb") as f_in:
    with gzip.open(GZIP_FILE, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

os.remove(ARCHIVE_FILE)

print("[OK] Nen gzip thanh cong")

# =========================
# 3. AES-256
# =========================

print("[3/4] Dang ma hoa AES-256...")

subprocess.run([
    "openssl",
    "enc",
    "-aes-256-cbc",
    "-salt",
    "-pbkdf2",
    "-in", GZIP_FILE,
    "-out", ENCRYPTED_FILE,
    "-pass", f"pass:{ENCRYPTION_KEY}"
], check=True)

os.remove(GZIP_FILE)

print("[OK] AES-256 encryption thanh cong")

# =========================
# 4. UPLOAD S3
# =========================

print("[4/4] Dang upload len Amazon S3...")

# QUAN TRỌNG:
# Ép boto3 sử dụng region ap-southeast-2
session = boto3.Session(
    region_name=AWS_REGION
)

s3 = session.client(
    "s3",
    region_name=AWS_REGION
)

print("[INFO] S3 endpoint:", s3.meta.endpoint_url)

S3_KEY = (
    f"provincial-center/"
    f"mongodb/"
    f"{TIMESTAMP}/"
    f"{os.path.basename(ENCRYPTED_FILE)}"
)

s3.upload_file(
    ENCRYPTED_FILE,
    S3_BUCKET,
    S3_KEY
)

print("[OK] Upload S3 thanh cong")

print()
print("=" * 50)
print("BACKUP HOAN THANH")
print("=" * 50)
print(f"S3: s3://{S3_BUCKET}/{S3_KEY}")

# =========================
# CLEANUP
# =========================

if os.path.exists(ENCRYPTED_FILE):
    os.remove(ENCRYPTED_FILE)

print("[OK] Da xoa file tam")
