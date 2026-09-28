import os
import gzip
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

import boto3


MONGODB_URI = os.environ["MONGODB_URI"]
S3_BUCKET = os.environ["S3_BUCKET"]
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
ENCRYPTION_KEY = os.environ["BACKUP_ENCRYPTION_KEY"]

DB_NAME = "cloud_dr"
S3_PREFIX = "mongodb"

BACKUP_DIR = "backup"

os.makedirs(BACKUP_DIR, exist_ok=True)

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

archive_file = os.path.join(
    BACKUP_DIR,
    f"cloud_dr_{timestamp}.archive"
)

gzip_file = archive_file + ".gz"

encrypted_file = gzip_file + ".enc"


print("=" * 60)
print("MONGODB DISASTER RECOVERY BACKUP")
print("=" * 60)


try:

    print("[1/4] Dang backup MongoDB...")

    subprocess.run(
        [
            "mongodump",
            f"--uri={MONGODB_URI}",
            f"--db={DB_NAME}",
            f"--archive={archive_file}"
        ],
        check=True
    )

    print("[OK] MongoDB backup thanh cong")


    print("[2/4] Dang nen backup...")

    with open(archive_file, "rb") as source:

        with gzip.open(gzip_file, "wb") as target:

            shutil.copyfileobj(source, target)

    os.remove(archive_file)

    print("[OK] Nen gzip thanh cong")


    print("[3/4] Dang ma hoa AES-256...")

    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        encoding="utf-8"
    ) as key_file:

        key_file.write(ENCRYPTION_KEY.strip())

        key_file_path = key_file.name


    try:

        subprocess.run(
            [
                "openssl",
                "enc",
                "-aes-256-cbc",
                "-pbkdf2",
                "-iter",
                "100000",
                "-salt",
                "-in",
                gzip_file,
                "-out",
                encrypted_file,
                "-pass",
                f"file:{key_file_path}"
            ],
            check=True
        )

    finally:

        if os.path.exists(key_file_path):
            os.remove(key_file_path)


    os.remove(gzip_file)

    print("[OK] AES-256 encryption thanh cong")


    print("[4/4] Dang upload len Amazon S3...")

    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION
    )

    s3_key = f"{S3_PREFIX}/{os.path.basename(encrypted_file)}"

    s3.upload_file(
        encrypted_file,
        S3_BUCKET,
        s3_key
    )

    print("[OK] Upload S3 thanh cong")

    print("-" * 60)

    print(f"S3 Bucket : {S3_BUCKET}")
    print(f"S3 Object : {s3_key}")
    print(f"Local File: {encrypted_file}")

    print("=" * 60)
    print("BACKUP HOAN TAT")
    print("=" * 60)


except Exception as error:

    print("[ERROR]", error)

    raise