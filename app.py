import ipaddress
import logging
import os
import ssl
import threading
from typing import Any
from urllib.parse import urlparse
from flask import Flask, jsonify, render_template, request, Response, send_file, send_from_directory
from werkzeug.security import safe_join
from src.downloader import SoundVaultDownloader

logger = logging.getLogger(__name__)

app = Flask(__name__)

DOWNLOAD_DIR = os.path.abspath("downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def background_download(url: str, audio_format: str, quality: str) -> None:
    try:
        downloader = SoundVaultDownloader()
        if hasattr(downloader, "config"):
            downloader.config["audio_format"] = audio_format
            downloader.config["audio_quality"] = quality
            downloader.config["output_path"] = DOWNLOAD_DIR
            downloader.config["download_dir"] = DOWNLOAD_DIR
        if hasattr(downloader, "download_dir"):
            downloader.download_dir = DOWNLOAD_DIR

        downloader.download(url)
        logger.info("Download erfolgreich abgeschlossen!")
    except Exception as e:
        logger.error(f"Background download error: {e}")


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/files", methods=["GET"])
def list_files() -> Response:
    files: list[dict[str, Any]] = []
    supported_extensions = ('.mp3', '.webm', '.m4a', '.flac', '.wav', '.opus')

    if os.path.exists(DOWNLOAD_DIR):
        for root, dirs, filenames in os.walk(DOWNLOAD_DIR):
            for f in filenames:
                if f.lower().endswith(supported_extensions):
                    file_path = os.path.join(root, f)
                    if os.path.isfile(file_path):
                        try:
                            relative_path = os.path.relpath(file_path, DOWNLOAD_DIR)
                            relative_path = relative_path.replace('\\', '/')
                            files.append({
                                "name": f,
                                "path": relative_path,
                                "size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2)
                            })
                        except (OSError, ValueError) as e:
                            logger.warning(f"Could not process file {f}: {e}")

    return jsonify(sorted(files, key=lambda x: x["name"]))


@app.route("/api/files/download/<path:filepath>", methods=["GET"])
def get_file(filepath: str) -> Response:
    supported_extensions = ('.mp3', '.webm', '.m4a', '.flac', '.wav', '.opus')
    if not filepath.lower().endswith(supported_extensions):
        return jsonify({"error": "Ungültiger Dateityp"}), 400

    filepath = filepath.replace('/', os.sep)
    safe_path = os.path.abspath(os.path.join(DOWNLOAD_DIR, filepath))

    if not safe_path.startswith(DOWNLOAD_DIR):
        return jsonify({"error": "Ungültiger Pfad"}), 403

    if not os.path.isfile(safe_path):
        return jsonify({"error": "Datei nicht gefunden"}), 404

    return send_file(safe_path, as_attachment=True, download_name=os.path.basename(safe_path))


@app.route("/api/download", methods=["POST"])
def start_download() -> Response:
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    audio_format = data.get("format", "mp3")
    quality = data.get("quality", "320")

    if not url:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    parsed = urlparse(url)
    if not all([parsed.scheme in ('http', 'https'), parsed.netloc]):
        return jsonify({"status": "error", "message": "Invalid URL"}), 400

    thread = threading.Thread(
        target=background_download, args=(url, audio_format, quality), daemon=True
    )
    thread.start()

    return jsonify(
        {
            "status": "success",
            "message": f"Download gestartet: {url}",
        }
    )


if __name__ == "__main__":
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    cert_file = "cert.pem"
    key_file = "key.pem"

    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime

        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Berlin"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Berlin"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SoundVault"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
            ]),
            critical=False,
        ).sign(key, hashes.SHA256())

        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        logger.info("Self-signed SSL certificate generated.")

    app.run(host="0.0.0.0", port=5000, ssl_context=(cert_file, key_file), debug=False)