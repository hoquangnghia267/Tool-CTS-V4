from cryptography import x509
from cryptography.hazmat.backends import default_backend
import sys
import os
import datetime
import pytz  # pip install pytz

def read_cert_info(cert_path):
    if not os.path.exists(cert_path):
        print("File không tồn tại:", cert_path)
        return

    with open(cert_path, 'rb') as f:
        cert_data = f.read()

    try:
        if b"BEGIN CERTIFICATE" in cert_data:
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        else:
            cert = x509.load_der_x509_certificate(cert_data, default_backend())
    except Exception as e:
        print("Lỗi khi đọc chứng chỉ:", e)
        return

    # Mặc định là UTC
    not_before_utc = cert.not_valid_before_utc
    not_after_utc = cert.not_valid_after_utc


    # Chuyển sang múi giờ GMT+7
    gmt_plus7 = pytz.timezone("Asia/Ho_Chi_Minh")
    not_before_gmt7 = not_before_utc.astimezone(gmt_plus7)
    not_after_gmt7 = not_after_utc.astimezone(gmt_plus7)

    # Lấy timestamp theo GMT+7 (vẫn tính từ epoch UTC, chỉ là chuyển giờ để hiển thị)
    not_before_ms = int(not_before_gmt7.timestamp() * 1000)
    not_after_ms = int(not_after_gmt7.timestamp() * 1000)

    print(f"Ngày bắt đầu (GMT+7): {not_before_gmt7} => {not_before_ms} ms")
    print(f"Ngày kết thúc (GMT+7): {not_after_gmt7} => {not_after_ms} ms")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Cách dùng: python app.py <duong_dan_chung_chi>")
    else:
        read_cert_info(sys.argv[1])
