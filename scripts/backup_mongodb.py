import os
import gzip
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone


# ============================================================
# CẤU HÌNH
# ============================================================

MONGODB_URI = os.environ["MONGODB_URI"]
ENCRYPTION_KEY = os.environ["BACKUP_ENCRYPTION_KEY"]

DB_NAME = "cloud_dr"
BACKUP_DIR = "backup"

os.makedirs(BACKUP_DIR, exist_ok=True)

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

archive_file = os.path.join(
    BACKUP_DIR,
    f"cloud_dr_{timestamp}.archive"
)

gzip_file = archive_file + ".gz"

encrypted_file = gzip_file + ".enc"


# ============================================================
# BẮT ĐẦU BACKUP
# ============================================================

print("=" * 60)
print("MONGODB DISASTER RECOVERY BACKUP")
print("=" * 60)


try:

    # ========================================================
    # BƯỚC 1: BACKUP MONGODB
    # ========================================================

    print("[1/3] Dang backup MongoDB...")

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


    # ========================================================
    # BƯỚC 2: NÉN GZIP
    # ========================================================

    print("[2/3] Dang nen backup...")

    with open(archive_file, "rb") as source:

        with gzip.open(gzip_file, "wb") as target:

            shutil.copyfileobj(source, target)

    os.remove(archive_file)

    print("[OK] Nen gzip thanh cong")


    # ========================================================
    # BƯỚC 3: MÃ HÓA AES-256
    # ========================================================

    print("[3/3] Dang ma hoa AES-256...")

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


    # ========================================================
    # HOÀN TẤT
    # ========================================================

    print("-" * 60)

    print(f"Encrypted backup: {encrypted_file}")

    print("-" * 60)

    print("BACKUP HOAN TAT")

    print("=" * 60)


except Exception as error:

    print("[ERROR]", error)

    raise