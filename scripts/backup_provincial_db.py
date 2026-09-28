import os
import subprocess
import datetime
import boto3

DATABASES = [
    "CSDL_A_Dancu",
    "CSDL_B_Dichvucong",
    "CSDL_C_Datdai"
]

BACKUP_DIR = "/tmp/provincial_backups"
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

ENCRYPTION_KEY = os.getenv("BACKUP_ENCRYPTION_KEY")
S3_BUCKET = os.getenv("S3_DR_BACKUP_BUCKET")

os.makedirs(BACKUP_DIR, exist_ok=True)

s3 = boto3.client("s3")


def run_backup():

    for db in DATABASES:

        raw_file = f"{BACKUP_DIR}/{db}_{TIMESTAMP}.sql.gz"
        enc_file = f"{raw_file}.enc"

        print(f"[BACKUP] {db}")

        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD

        dump_cmd = (
            f'pg_dump -h "{DB_HOST}" '
            f'-U "{DB_USER}" '
            f'-d "{db}" | gzip > "{raw_file}"'
        )

        subprocess.run(
            dump_cmd,
            shell=True,
            check=True,
            env=env
        )

        print(f"[ENCRYPT] AES-256 {db}")

        encrypt_cmd = [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-salt",
            "-pbkdf2",
            "-in",
            raw_file,
            "-out",
            enc_file,
            "-pass",
            f"pass:{ENCRYPTION_KEY}"
        ]

        subprocess.run(encrypt_cmd, check=True)

        s3_key = (
            f"provincial-center/"
            f"{db}/"
            f"{TIMESTAMP}/"
            f"{os.path.basename(enc_file)}"
        )

        print(f"[UPLOAD] {s3_key}")

        s3.upload_file(
            enc_file,
            S3_BUCKET,
            s3_key
        )

        print(f"[SUCCESS] {db}")

        os.remove(raw_file)
        os.remove(enc_file)


if __name__ == "__main__":
    run_backup()
