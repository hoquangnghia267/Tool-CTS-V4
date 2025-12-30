import os
import subprocess
import sys
import time
import mysql.connector
import time
import requests
import logging
import tkinter as tk
from tkinter import messagebox
from database import connect_to_database, get_database_config
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.hashes import SHA256, SHA1
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.x509 import load_pem_x509_certificate, ocsp, ExtensionOID, AuthorityInformationAccessOID, oid
from cryptography.x509.oid import AuthorityInformationAccessOID, ExtendedKeyUsageOID
from cryptography.x509.ocsp import OCSPRequestBuilder, OCSPCertStatus, OCSPResponseStatus, load_der_ocsp_response


def get_text_data(text_widget):
    return text_widget.get("1.0", tk.END).strip().split('\n')

def get_text_single(text_widget):
    return text_widget.get("1.0", tk.END).strip()

def hex_to_decimal(hex_string):
    try:
        return int(hex_string, 16)
    except ValueError:
        return None

def decimal_to_hex(decimal_number):
    try:
        hex_string = format(int(decimal_number), 'X')
        return hex_string
    except ValueError:
        print("Error: Invalid decimal number.")
        return None

def hex_to_decimal_list(hex_serials):
    decimal_serials = []
    for hex_serial in hex_serials:
        decimal_serial = hex_to_decimal(hex_serial.strip())
        if decimal_serial is not None:
            decimal_serials.append(str(decimal_serial))
    return decimal_serials


# def setup_logging(section_name, log_dir="log"):
#     log_dir = os.path.join(log_dir, "")
#     os.makedirs(log_dir, exist_ok=True)
#     current_date = datetime.now().date()

#     log_file = os.path.join(log_dir, f"{current_date}.{section_name}.log")

#     formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

#     file_handler = logging.FileHandler(log_file, mode="a")
#     file_handler.setLevel(logging.INFO)
#     file_handler.setFormatter(formatter)

#     logger = logging.getLogger(section_name)
#     logger.setLevel(logging.INFO)
#     logger.addHandler(file_handler)

#     return logger
def setup_logging(section_name, base_log_dir="log"):
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")

    # Tạo đường dẫn thư mục: log/YYYY/MM
    log_dir = os.path.join(base_log_dir, year, month)
    os.makedirs(log_dir, exist_ok=True)

    # Tạo tên file log: section_name.log
    log_file = os.path.join(log_dir, f"{section_name}.log")

    # Định dạng log
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Logger
    logger = logging.getLogger(section_name)

    # Tránh gắn nhiều handler nếu đã có
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.propagate = False  # Không ghi đúp ra console nếu có logger root

    return logger

def convert_timestamp_to_gmt7(timestamp):

    try:
        # Convert timestamp to datetime object
        dt = datetime.fromtimestamp(timestamp / 1000.0, timezone.utc)
        # Add 7 hours to switch to GMT+07 time zone
        dt = dt + timedelta(hours=7)
        # Convert to GMT+07 format time string
        gmt7_time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        return gmt7_time_str
    except:
        return "Invalid Timestamp"

def get_current_timestamp_in_gmt_plus_7():
    # Lấy thời gian hiện tại theo UTC
    current_utc_time = datetime.utcnow()
    
    # Tạo một timezone cho GMT+7
    gmt_plus_7 = timezone(timedelta(hours=7))
    
    # Chuyển đổi thời gian hiện tại sang GMT+7
    current_gmt_plus_7_time = current_utc_time.replace(tzinfo=timezone.utc).astimezone(gmt_plus_7)
    
    # Chuyển đổi thời gian hiện tại sang timestamp
    current_timestamp_gmt_plus_7 = int(current_gmt_plus_7_time.timestamp() * 1000)
    
    return current_timestamp_gmt_plus_7
    
#-----CTS-----
def query_info_cts(conn, decimal_serials):
    try:
        cursor = conn.cursor()

        # Chuyển đổi các giá trị decimal sang chuỗi có dấu nháy đơn
        formatted_serials = "','".join(str(sn) for sn in decimal_serials)
        query = f"""
            SELECT serialNumber, status, revocationDate, expireDate, subjectDN, username
            FROM CertificateData
            WHERE serialNumber IN ('{formatted_serials}')
        """
        cursor.execute(query)
        results = cursor.fetchall()

        cursor.close()
        
        return results
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
 

def update_revoked_list(conn, serial_data, revocation_data, logger):
    try:
        start_time = time.time()
        cursor = conn.cursor()

        if len(serial_data) != len(revocation_data):
            raise ValueError("Number of serial numbers and revocation dates must be the same")
        
        updated_columns = 0
        not_updated = 0
        # Loop through each pair of serial number and revocation date to perform the update
        for serial, revocation in zip(serial_data, revocation_data):
            serial_decimal = hex_to_decimal(serial)

            sql = """
                UPDATE CertificateData 
                SET revocationReason = 1, status = 40, rowVersion = 1, revocationDate = %s
                WHERE expireDate > %s AND status = 20 AND serialNumber = '%s';
            """
            cursor.execute(sql, (revocation, revocation, serial_decimal))
            if cursor.rowcount > 0:
                logger.info(f"Revoke   - {serial} - {revocation}")
                updated_columns += cursor.rowcount
            else:
                select_sql2 = """
                    SELECT serialNumber, status, revocationDate FROM CertificateData
                    WHERE serialNumber = '%s';
                """
                cursor.execute(select_sql2, (serial_decimal,))
                result = cursor.fetchone()
                if result:
                    logger.warning(f"No update - {serial} - Status: {result[1]}, Revocation Date: {result[2]}")
                else:
                    logger.warning(f"No update - {serial} - Record not found")
                not_updated += 1
        
        # Commit and close the connection
        conn.commit()
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 1)

        messagebox.showinfo("Success", f"Updated {updated_columns} records in {elapsed_time} seconds")
        logger.info(f"Updated {updated_columns} records in {elapsed_time} seconds")
        logger.info(f"No updates for {not_updated} records")
        cursor.close()
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"MySQL Error: {str(e)}")
        logger.error(f"MySQL Error: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        logger.error(f"An error occurred: {str(e)}")
    finally:
        if cursor:
            cursor.close()


def update_revoked_list_force(conn, serial_data, revocation_data, logger):
    try:
        start_time = time.time()
        cursor = conn.cursor()

        if len(serial_data) != len(revocation_data):
            raise ValueError("Number of serial numbers and revocation dates must be the same")
        
        updated_columns = 0
        not_updated = 0
        # Loop through each pair of serial number and revocation date to perform the update
        for serial, revocation in zip(serial_data, revocation_data):
            serial_decimal = hex_to_decimal(serial)

            sql = """
                UPDATE CertificateData 
                SET revocationReason = 1, status = 40, rowVersion = 1, revocationDate = %s
                WHERE status = 20 AND serialNumber = '%s';
            """
            cursor.execute(sql, (revocation, serial_decimal))
            if cursor.rowcount > 0:
                logger.info(f"Revoke   - {serial} - {revocation}")
                updated_columns += cursor.rowcount
            else:
                select_sql2 = """
                    SELECT serialNumber, status, revocationDate FROM CertificateData
                    WHERE serialNumber = '%s';
                """
                cursor.execute(select_sql2, (serial_decimal,))
                result = cursor.fetchone()
                if result:
                    logger.warning(f"No update - {serial} - Status: {result[1]}, Revocation Date: {result[2]}")
                else:
                    logger.warning(f"No update - {serial} - Record not found")
                not_updated += 1
        
        # Commit and close the connection
        conn.commit()
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 1)

        messagebox.showinfo("Success", f"Updated {updated_columns} records in {elapsed_time} seconds")
        logger.info(f"Updated {updated_columns} records in {elapsed_time} seconds")
        logger.info(f"No updates for {not_updated} records")
        cursor.close()
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"MySQL Error: {str(e)}")
        logger.error(f"MySQL Error: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        logger.error(f"An error occurred: {str(e)}")
    finally:
        if cursor:
            cursor.close()


def update_revoked_list_new(conn, serial_data, revocationDate, logger):
    try:
        revocation_date = revocationDate
        decimal_serials = hex_to_decimal_list(serial_data)
        decimal_serials_str = "','".join(decimal_serials)

        start_time = time.time()
        updated_columns = 0
        cursor = conn.cursor()

        # Truy vấn trước để lấy các serial tồn tại trong cơ sở dữ liệu
        pre_sql = """
            SELECT serialNumber FROM CertificateData
            WHERE serialNumber IN %s;
        """
        cursor.execute(pre_sql % (f"('{decimal_serials_str}')",))
        select_rows = cursor.fetchall()

        if select_rows:
            found_serials = {str(row[0]) for row in select_rows}  # Tạo tập hợp các serial number tìm thấy

            # Tìm các serial number không có trong kết quả
            not_found_serials = [sn for sn in decimal_serials if sn not in found_serials]
            
            if not_found_serials:
                logger.info("\nSerials not found in database:")
                for sn in not_found_serials:
                    logger.info(f"{decimal_to_hex(sn)}")
        else:
            logger.info("\nSerials not found in database:")
            for sn in decimal_serials:
                logger.info(f"{decimal_to_hex(sn)}")
            return  # Không thực hiện cập nhật nếu không có serial nào tồn tại trong cơ sở dữ liệu

        # Thực hiện cập nhật
        sql = """
            UPDATE CertificateData 
            SET revocationReason = 1, status = 40, rowVersion = 1, revocationDate = %s
            WHERE serialNumber IN %s 
                AND status = 20 
                AND expireDate > %s;
        """
        cursor.execute(sql % (revocation_date, f"('{decimal_serials_str}')", revocation_date))
        updated_columns += cursor.rowcount
        conn.commit()
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 1)

        # Log các serial đã được cập nhật thành công
        logger.info(f"\nUpdated {updated_columns} records in {elapsed_time} seconds")
        select_sql = """
            SELECT serialNumber, status, revocationDate FROM CertificateData
            WHERE serialNumber IN %s 
                AND status = 40 
                AND revocationDate = %s;
        """
        cursor.execute(select_sql % (f"('{decimal_serials_str}')", revocation_date,))
        select_rows = cursor.fetchall()
        for row in select_rows:
            serial_dec = decimal_to_hex(row[0])
            status = row[1]
            revocation_date = row[2]
            logger.info(f"Revoked: {serial_dec} - status: {status} - revocationDate: {revocation_date}")
     
        
        # Log các serial chưa được cập nhật
        logger.info("Serial numbers have not been updated:")
        select_sql2 = """
            SELECT serialNumber, status, revocationDate FROM CertificateData
            WHERE serialNumber IN %s
                AND (status = 20 OR (status = 40 AND revocationDate <> %s));
                
        """
        cursor.execute(select_sql2 % (f"('{decimal_serials_str}')", revocation_date,))
        select_rows_2 = cursor.fetchall()
        for row in select_rows_2:
            serial_dec = decimal_to_hex(row[0])
            status = row[1]
            revocation_date = row[2]
            logger.info(f"Not updated: {serial_dec} - status: {status} - revocationDate: {revocation_date}")

        messagebox.showinfo("Success", f"Updated {updated_columns} records in {elapsed_time} seconds")

    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"MySQL Error: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        if cursor:
            cursor.close()


def update_unrevoked_list(conn, serial_data, logger):
    try:
        logger.info("---------------Start updating---------------")
        decimal_serials = hex_to_decimal_list(serial_data)
        decimal_serials_str = "','".join(decimal_serials)
        start_time = time.time()

        cursor = conn.cursor()

        # Trước khi unrevoke, ghi log ngay revoke
        pre_sql = """
            SELECT serialNumber, status, revocationDate FROM CertificateData
            WHERE serialNumber IN %s;
        """
        cursor.execute(pre_sql % (f"('{decimal_serials_str}')",))
        select_rows = cursor.fetchall()

        if select_rows:
            found_serials = {str(row[0]) for row in select_rows}  # Tạo tập hợp các serial number tìm thấy
            for row in select_rows:
                serial_dec = decimal_to_hex(row[0])
                status = row[1]
                revocation_date = row[2]
                logger.info(f"Pre_Unrevoke - {serial_dec} - status: {status} - revocationDate: {revocation_date}")
            # Tìm các serial number không có trong kết quả
            not_found_serials = [sn for sn in decimal_serials if sn not in found_serials]
            
            if not_found_serials:
                logger.info("---------------Serials not found in database---------------")
                for sn in not_found_serials:
                    logger.info(f"{decimal_to_hex(sn)}")
        else:
            messagebox.showinfo("No Results", "No data found for the provided serial numbers.")
        logger.info("-----------------------------------------------------------")    
        # Thực hiện update Unrevoke
        pre_update_serials = found_serials.copy()  # Lưu danh sách serials trước khi cập nhật
        updated_columns = 0
        current_time = get_current_timestamp_in_gmt_plus_7()
        sql = """
            UPDATE CertificateData 
            SET revocationDate = -1, revocationReason = -1, status = 20, rowVersion = 0
            WHERE status in (40, 60) AND serialNumber IN %s AND expireDate > %s 
        """
        cursor.execute(sql % (f"('{decimal_serials_str}')", current_time))
        updated_columns += cursor.rowcount
        conn.commit()

        select_sql = """
            SELECT serialNumber, status, revocationDate FROM CertificateData
            WHERE serialNumber IN %s;
        """
        cursor.execute(select_sql % (f"('{decimal_serials_str}')",))
        updated_rows = cursor.fetchall()

        # Tạo tập hợp các serial number đã được cập nhật thành công
        updated_serials = {str(row[0]) for row in updated_rows if row[1] == 20}

        # Ghi log các serial number không được cập nhật (không có trạng thái 20)
        not_updated_serials = pre_update_serials - updated_serials
        if not_updated_serials:
            logger.info("---------------Serials NOT updated to status 20---------------")
            for sn in not_updated_serials:
                logger.info(f"{decimal_to_hex(sn)}")

        # Ghi log các serial number đã được cập nhật thành công
        logger.info("---------------Serials updated to status 20---------------")
        for row in updated_rows:
            serial_dec = decimal_to_hex(row[0])
            status = row[1]
            revocation_date = row[2]
            
            if status == 20:
                logger.info(f"Unrevoke - {serial_dec} - status: {status} - revocationDate: {revocation_date}")
            # else:
            #     logger.info(f"Pre_Unrevoke - {serial_dec} - status: {status} - revocationDate: {revocation_date}")
        logger.info("---------------Complete update unrevoked data !---------------")
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 1)
        
        messagebox.showinfo("Success", f"Updated {updated_columns} records in {elapsed_time} seconds")
        cursor.close()
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"MySQL Error: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        if cursor:
            cursor.close()



#-----TMS1-----
def get_info_TMS1(conn, tokenid, get_result_text):
    if tokenid is not None:
        cursor = conn.cursor()
        query = "SELECT isPushNotice, MST, SubjectName, NoticeInfo, IsBlock, IsUnblock FROM token WHERE TokenID = %s;"
        cursor.execute(query, (tokenid,))
        results = cursor.fetchall()
        if results:
            result_str = ""
            for row in results:
                isPushNotice = row[0]              
                MST = row[1]
                SubjectName = row[2]
                NoticeInfo = row[3]
                IsBlock = row[4]
                IsUnblock = row[5]
                result_str += f"Token ID: {tokenid}\n"
                result_str += f"MST: {MST}\n"
                result_str += f"Tên công ty: {SubjectName}\n"
                result_str += f"IsUnblock: {IsUnblock}\n"
                if isPushNotice == 0:
                    result_str += "Trạng thái thông báo: OFF\n"
                elif isPushNotice == 1:
                    result_str += "Trạng thái thông báo: ON\n"
                else:
                    result_str += f"Trạng thái thông báo: {isPushNotice}\n"

                if IsBlock == 0:
                    result_str += "Trạng thái khóa: OFF\n"
                elif IsBlock == 1:
                    result_str += "Trạng thái khóa: ON\n"
                else:
                    result_str += f"Trạng thái khóa: {IsBlock}\n"

                result_str += f"Câu thông báo:\n{NoticeInfo}\n"
                
            get_result_text.config(state=tk.NORMAL)
            get_result_text.delete(1.0, tk.END)
            get_result_text.insert(tk.END, result_str)
            get_result_text.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("Thông báo", "Không tìm thấy Token ID đã nhập.")       
        cursor.close()

def note_hotro_tms1(conn, token_hid, content_text, logger):
    try:
        cursor = conn.cursor()

        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)

        # Tạo câu truy vấn cập nhật
        sql = f"UPDATE token SET isPushNotice=0, NoticeInfo = '{content_text}' WHERE TokenID IN ('{id_list}')"
        cursor.execute(sql)

        # Commit và đóng kết nối
        conn.commit()
        logger.info(f"{token_hid} - ON note page: hotro.smartsign.com.vn\n")
        messagebox.showinfo("Success", "Records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def notifications_tms1(conn, token_hid, content_text, logger):
    try:
        cursor = conn.cursor()

        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)

        # Tạo câu truy vấn cập nhật
        updated_columns = 0
        sql = f"UPDATE token SET isPushNotice=1, NoticeInfo = '{content_text}' WHERE TokenID IN ('{id_list}')"
        cursor.execute(sql)
        updated_columns += cursor.rowcount
        # Commit và đóng kết nối
        conn.commit()
        logger.info(f"{token_hid} - ON Notifications TMS1 \n")
        messagebox.showinfo("Success", f"{updated_columns} records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def off_notifications_tms1(conn, token_hid, logger):
    try:
        cursor = conn.cursor()
        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)
        # Tạo câu truy vấn cập nhật
        sql = f"UPDATE token SET isPushNotice = NULL, NoticeInfo = NULL WHERE TokenID IN ('{id_list}')"
        cursor.execute(sql)
        # Commit và đóng kết nối
        conn.commit()
        # Ghi log
        logger.info(f"{token_hid} - OFF Notifications TMS1 \n")
        messagebox.showinfo("Success", "Records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def block_tms1(conn, token_hid, note_text, logger):
    try:
        cursor = conn.cursor()

        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)

        # Tạo câu truy vấn cập nhật
        sql = f"UPDATE token SET IsBlock = 1, isPushNotice = 1, NoticeInfo = '{note_text}' WHERE TokenID IN ('{id_list}')"
        cursor.execute(sql)

        # Commit và đóng kết nối
        conn.commit()
        logger.info(f"{token_hid} - block \n")
        messagebox.showinfo("Success", "Records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def unblock_tms1(conn, token_hid, logger):
    try:
        cursor = conn.cursor()
        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)
        # Tạo câu truy vấn cập nhật
        sql = f"UPDATE token SET IsUnblock = 1, isPushNotice = NULL, NoticeInfo = NULL WHERE TokenID IN ('{id_list}')"
        cursor.execute(sql)
        # Commit và đóng kết nối
        conn.commit()
        # Ghi log
        logger.info(f"{token_hid} - unblock \n")
        messagebox.showinfo("Success", "Records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

#-----TMS2-----
def get_info_TMS2(conn, tokenid, get_result_text):
    if tokenid is not None:
        cursor = conn.cursor()
        query = "SELECT use_specific_notification, token_block_status, token_title, token_notification, token_note FROM token_ms WHERE token_hid = %s;"
        cursor.execute(query, (tokenid,))
        results = cursor.fetchall()
        if results:
            result_str = ""
            for row in results:
                use_specific_notification = row[0]              
                token_block_status = row[1]
                token_title = row[2]
                token_notification = row[3]
                token_note = row[4]
                result_str += f"Token ID: {tokenid}\n"
                if use_specific_notification == 0:
                    result_str += "Trạng thái thông báo: OFF\n"
                elif use_specific_notification == 1:
                    result_str += "Trạng thái thông báo: ON\n"
                else:
                    result_str += f"Trạng thái thông báo: {use_specific_notification}\n"

                if token_block_status == 0:
                    result_str += "Trạng thái khóa: OFF\n"
                elif token_block_status == 1:
                    result_str += "Trạng thái khóa: ON\n"
                else:
                    result_str += f"Trạng thái khóa: {token_block_status}\n"

                result_str += f"Câu thông báo:\nTiêu đề: {token_title}\nNội dung: {token_notification}\n"
                result_str += f"Note: {token_note}"

            get_result_text.config(state=tk.NORMAL)
            get_result_text.delete(1.0, tk.END)
            get_result_text.insert(tk.END, result_str)
            get_result_text.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("Thông báo", "Không tìm thấy Token ID đã nhập.")       
        cursor.close()

def block_tms2(conn, token_hid, note_text, logger):
    try:
        cursor = conn.cursor()

        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)
        updated_columns = 0
        # Tạo câu truy vấn cập nhật
        sql = f"UPDATE token_ms SET token_block_status = 1, token_note = '{note_text}' WHERE token_hid IN ('{id_list}')"
        cursor.execute(sql)
        updated_columns += cursor.rowcount
        # Commit và đóng kết nối
        conn.commit()
        logger.info(f"{token_hid} - block \n")
        messagebox.showinfo("Success", f"{updated_columns} records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def unblock_tms2(conn, token_hid, logger):
    try:
        cursor = conn.cursor()
        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)
        updated_columns = 0
        # Tạo câu truy vấn cập nhật
        sql = f"UPDATE token_ms SET token_block_status = 0, token_note = NULL WHERE token_hid IN ('{id_list}')"
        cursor.execute(sql)
        updated_columns += cursor.rowcount
        # Commit và đóng kết nối       
        conn.commit()
        # Ghi log
        logger.info(f"{token_hid} - unblock \n")
        messagebox.showinfo("Success", f"{updated_columns} records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
  
def notifications_tms2(conn, token_hid, title_text, content_text, logger):
    try:
        cursor = conn.cursor()

        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)
        updated_columns = 0
        # Tạo câu truy vấn cập nhật
        #sql = f"UPDATE token_ms SET use_specific_notification = 1, token_notification_status = 1, token_valid_from = CURDATE(),	token_valid_to = ADDDATE(CURDATE(),Interval 30 DAY), token_title = '{title_text}', token_notification = '{content_text}' WHERE token_hid IN ('{id_list}')"
        sql = f"UPDATE token_ms SET use_specific_notification = 1, token_notification_status = 1, token_valid_from = CURDATE(),	token_valid_to = '2025-05-19 23:59:59', token_title = '{title_text}', token_notification = '{content_text}' WHERE token_hid IN ('{id_list}')"
       
        cursor.execute(sql)
        updated_columns += cursor.rowcount
        # Commit và đóng kết nối
        conn.commit()
        logger.info(f"{token_hid} - ON Notifications TMS2 \n")
        messagebox.showinfo("Success", f"{updated_columns} records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def off_notifications_tms2(conn, token_hid, logger):
    try:
        cursor = conn.cursor()
        # Chuyển danh sách các id thành chuỗi định dạng ('id1', 'id2', 'id3', ...)
        id_list = "','".join(token_hid)
        # Tạo câu truy vấn cập nhật
        sql = f"UPDATE token_ms SET use_specific_notification = NULL, token_notification_status = 0, token_valid_from = NULL, token_valid_to = NULL, token_title = NULL, token_notification = NULL WHERE token_hid IN ('{id_list}')"
        cursor.execute(sql)
        # Commit và đóng kết nối
        conn.commit()
        # Ghi log
        logger.info(f"{token_hid} - OFF Notifications TMS2 \n")
        messagebox.showinfo("Success", "Records updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

#-----CTS-----
def get_serial_from_taxcode(conn, taxcode, get_result_text):
    if taxcode is not None:
        cursor = conn.cursor()
        query = "SELECT serialNumber, expireDate, status, username, subjectDN FROM CertificateData WHERE subjectDN LIKE %s ORDER BY expireDate DESC;"
        cursor.execute(query, (f"%{taxcode}%",))
        results = cursor.fetchall()
        if results:
            result_str = ""
            for row in results:
                serial_dec = row[0]
                serial_hex = decimal_to_hex(serial_dec)
                expire_date = row[1]
                expire_date_gmt7 = convert_timestamp_to_gmt7(expire_date)
                status = row[2]
                username = row[3]
                subjectdn = row[4]                    
                result_str += f"Serial Number: {serial_hex}\nExpire Date: {expire_date_gmt7}\nStatus: {status}\nUsername: {username}\nSubjectDN: {subjectdn}\n--------------\n"
            get_result_text.config(state=tk.NORMAL)
            get_result_text.delete(1.0, tk.END)
            get_result_text.insert(tk.END, result_str)
            get_result_text.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("Thông báo", "Không tìm thấy MST đã nhập.")       
        cursor.close()


def query_database(conn, serial_entry, result_text):
    cursor = conn.cursor()
    serial_hex = serial_entry.get()
    serial_decimal = hex_to_decimal(serial_hex)

    if serial_decimal is not None:
        query = """
            SELECT serialNumber, status, revocationDate, expireDate, subjectDN
            FROM CertificateData 
            WHERE serialNumber = '%s';
        """
        cursor.execute(query, (serial_decimal,))

        results = cursor.fetchall()
        if results:
            result_str = ""
            for row in results:
                serial_hex = decimal_to_hex(row[0])
                status = row[1]
                revocation_date = row[2]
                expire_date = row[3]
                subjectDN = row[4]
                # notBefore = row[5]
                # notBefore_gmt7 = convert_timestamp_to_gmt7(notBefore)
                expire_date_gmt7 = convert_timestamp_to_gmt7(expire_date)
                if revocation_date != -1:
                    revocation_date_gmt7 = convert_timestamp_to_gmt7(revocation_date)
                    result_str += f"Serial: {serial_hex}\nStatus: {status}\nRevocation Date (GMT+07): {revocation_date_gmt7}\nValid to: {expire_date_gmt7}\nSubjectDN: {subjectDN}\n"                    
                else:
                    result_str += f"Serial: {serial_hex}\nStatus: {status}\nRevocation Date: {revocation_date}\nValid to: {expire_date_gmt7}\nSubjectDN: {subjectDN}\n"
                    
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, result_str)
            result_text.config(state=tk.DISABLED) 
        else:
            messagebox.showinfo("Thông báo", "Không tìm thấy dữ liệu cho serialNumber đã nhập.")
        cursor.close()

def unrevoke_certificate(conn, serial_entry, section_name, logger):
    cursor = conn.cursor()
    serial_hex = serial_entry.get()
    serial_decimal = hex_to_decimal(serial_hex)
    
    if serial_decimal is not None:
        # Retrieve the current revocationDate from the database
        query = "SELECT revocationDate FROM CertificateData WHERE serialNumber = '%s';"
        cursor.execute(query, (serial_decimal,))
        result = cursor.fetchone()
        if result:
            current_revocation_date = result[0]
        else:
            current_revocation_date = None

        # Perform the update query
        update_query = "UPDATE CertificateData SET revocationDate = -1, revocationReason = -1, status = 20, rowVersion = 0 WHERE serialNumber = '%s';"
        cursor.execute(update_query, (serial_decimal,))
        conn.commit()

        # Log the action
        logger.info(f"Unrevoke - {serial_hex} - {current_revocation_date}")
        messagebox.showinfo("Thông báo", f"Unrevoke thành công vào cơ sở dữ liệu: {section_name}.")
        cursor.close()

#

def unrevoke_certificate_2(serial_entry):
    section_name2 = "OCSPv4"  # Đổi tên section tại đây nếu muốn kết nối đến cơ sở dữ liệu khác
    logger = setup_logging(section_name2)
    database_config2 = get_database_config(section_name2)
    conn2 = connect_to_database(database_config2)
    cursor2 = conn2.cursor()
    

    serial_hex = serial_entry.get()
    serial_decimal = hex_to_decimal(serial_hex)

    if serial_decimal is not None:
        # Retrieve the current revocationDate from the database
        query = "SELECT revocationDate FROM CertificateData WHERE serialNumber = '%s';"
        cursor2.execute(query, (serial_decimal,))
        result = cursor2.fetchone()
        if result:
            current_revocation_date = result[0]
        else:
            current_revocation_date = None

        # Perform the update query
        update_query2 = "UPDATE CertificateData SET revocationDate = -1, revocationReason = -1, status = 20, rowVersion = 0 WHERE serialNumber = '%s';"
        cursor2.execute(update_query2, (serial_decimal,))
        conn2.commit()

        # Log the action
        logger.info(f"Unrevoke - {serial_hex} - {current_revocation_date}")
        messagebox.showinfo("Thông báo", f"Unrevoke thành công vào cơ sở dữ liệu: {section_name2}.")
        cursor2.close()
        conn2.close()

def unrevoke_certificate_update(conn, serial_entry, section_name, logger):    
    unrevoke_certificate(conn, serial_entry, section_name, logger)
    if "CAv4" in section_name:
        unrevoke_certificate_2(serial_entry)

def revoke_certificate(conn, serial_entry, chk_revoke_date, entry_revoke_date, section_name, logger):
    cursor = conn.cursor()
    serial_hex = serial_entry.get()
    serial_decimal = hex_to_decimal(serial_hex)
    if serial_decimal is not None:
        #current_time = int(time.time() * 1000)  # Thời gian hiện tại tính bằng mili giây
        current_time = get_current_timestamp_in_gmt_plus_7() #updated ngày revoke bị sai
        
        # Kiểm tra xem dấu tick đã được chọn hay chưa
        if chk_revoke_date.get():
            try:
                # Lấy ngày revoke từ widget nhập liệu
                revoke_date = int(entry_revoke_date.get())
            except ValueError:
                # Xử lý lỗi nếu ngày revoke không hợp lệ
                messagebox.showerror("Lỗi", "Ngày revoke không hợp lệ. Vui lòng nhập lại theo định dạng timestamp.")
                return
        else:
            # Nếu dấu tick không được chọn, sử dụng thời gian hiện tại làm ngày revoke
            revoke_date = current_time

        update_query = "UPDATE CertificateData SET revocationDate = %s, revocationReason = 1, status = 40, rowVersion = 1 WHERE serialNumber = '%s';"
        cursor.execute(update_query, (revoke_date, serial_decimal))
        conn.commit()
        cursor.close()
        # Log the action
        logger.info(f"Revoke   - {serial_hex} - {revoke_date}")
        messagebox.showinfo("Thông báo", f"Revoke thành công vào cơ sở dữ liệu: {section_name}.")

def revoke_certificate_2(serial_entry, chk_revoke_date, entry_revoke_date):
    section_name2 = "OCSPv4"  # Đổi tên section tại đây nếu muốn kết nối đến cơ sở dữ liệu khác
    logger = setup_logging(section_name2)
    database_config2 = get_database_config(section_name2)
    conn2 = connect_to_database(database_config2)
    cursor2 = conn2.cursor()
    
    serial_hex = serial_entry.get()
    serial_decimal = hex_to_decimal(serial_hex)

    if serial_decimal is not None:
        #current_time = int(time.time() * 1000)  # Thời gian hiện tại tính bằng mili giây
        current_time = get_current_timestamp_in_gmt_plus_7()
        
        # Kiểm tra xem dấu tick đã được chọn hay chưa
        if chk_revoke_date.get():
            try:
                # Lấy ngày revoke từ widget nhập liệu
                revoke_date = int(entry_revoke_date.get())
            except ValueError:
                # Xử lý lỗi nếu ngày revoke không hợp lệ
                messagebox.showerror("Lỗi", "Ngày revoke không hợp lệ. Vui lòng nhập lại theo định dạng timestamp.")
                return
        else:
            # Nếu dấu tick không được chọn, sử dụng thời gian hiện tại làm ngày revoke
            revoke_date = current_time

        update_query = "UPDATE CertificateData SET revocationDate = %s, revocationReason = 1, status = 40, rowVersion = 1 WHERE serialNumber = '%s';"
        cursor2.execute(update_query, (revoke_date, serial_decimal))
        conn2.commit()

        # Log the action
        logger.info(f"Revoke   - {serial_hex} - {revoke_date}")
        messagebox.showinfo("Thông báo", f"Revoke thành công vào cơ sở dữ liệu: {section_name2}.")
        cursor2.close()
        conn2.close()

def revoke_certificate_update(conn, serial_entry, chk_revoke_date, entry_revoke_date, section_name, logger):    
    revoke_certificate(conn, serial_entry, chk_revoke_date, entry_revoke_date, section_name, logger)
    if "CAv4" in section_name:
        revoke_certificate_2(serial_entry, chk_revoke_date, entry_revoke_date)

def export_base64_cert(conn, serial_entry):
    cursor = conn.cursor()   
    serial_hex = serial_entry.get()
    serial_decimal = hex_to_decimal(serial_hex)

    if serial_decimal is not None:
        query = "SELECT base64Cert FROM CertificateData WHERE serialNumber = '%s';"
        cursor.execute(query, (serial_decimal,))
        result = cursor.fetchone()
        
        if result:
            data = result[0]  # Lấy dữ liệu từ result
            file_name = f"{serial_hex}.cer"
            folder_path = "Certificates"  # Tên thư mục bạn muốn lưu vào

            # Tạo thư mục nếu chưa tồn tại
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Đường dẫn đầy đủ của tệp
            file_path = os.path.join(folder_path, file_name)

            with open(file_path, "w") as file:  
                file.write("-----BEGIN CERTIFICATE-----\n")  
                file.write(data)
                file.write("\n-----END CERTIFICATE-----") 
            messagebox.showinfo("Thông báo", f"Đã xuất dữ liệu vào tệp {file_path}")
        else:
            messagebox.showinfo("Thông báo", "Không tìm thấy dữ liệu cho serialNumber đã nhập.")
        cursor.close()
import os
from tkinter import messagebox

def export_base64_certificates(conn, serial_entries_input, logger):
    cursor = conn.cursor()

    # Kiểm tra nếu input là một danh sách hoặc một chuỗi
    if isinstance(serial_entries_input, list):
        serial_entries = serial_entries_input
    elif isinstance(serial_entries_input, str):
        serial_entries = serial_entries_input.split('\n')
    else:
        raise ValueError("Input phải là chuỗi hoặc danh sách các số serial.")

    for serial_hex in serial_entries:
        serial_hex = serial_hex.strip()  # Loại bỏ khoảng trắng đầu và cuối
        if not serial_hex:
            continue  # Bỏ qua các dòng trống

        serial_decimal = hex_to_decimal(serial_hex)

        if serial_decimal is not None:
            query = "SELECT base64Cert FROM CertificateData WHERE serialNumber = '%s';"
            cursor.execute(query, (serial_decimal,))
            result = cursor.fetchone()
            
            if result:
                data = result[0]
                file_name = f"{serial_hex}.cer"
                folder_path = "Certificates"

                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                file_path = os.path.join(folder_path, file_name)

                with open(file_path, "w") as file:
                    file.write("-----BEGIN CERTIFICATE-----\n")
                    file.write(data)
                    file.write("\n-----END CERTIFICATE-----")
                
                logger.info(f"Đã xuất dữ liệu vào tệp {file_path}")
            else:
                logger.warning(f"Không tìm thấy dữ liệu cho serialNumber {serial_hex}")
        
    cursor.close()


def query_cts_theo_tinh(conn, province_data):
    #-----vinacaold-----
    query_vinacaold_tongcapphat_DN = """
        SELECT	count(*) 
        FROM CertificateData 
        WHERE cAFingerprint = '3659c6ba7f9880a4660512db19fcf83fda42798e' 
            AND subjectDN LIKE '%UID=MST:%' 
            AND subjectDN LIKE %s;        
    """

    query_vinacaold_tongcapphat_CN = """
        SELECT	count(*) 
        FROM CertificateData 
        WHERE cAFingerprint = '3659c6ba7f9880a4660512db19fcf83fda42798e' 
            AND (subjectDN LIKE '%UID=CMND:%' OR subjectDN LIKE '%UID=CCCD:%' OR subjectDN LIKE '%UID=HC:%')
            AND subjectDN LIKE %s;     
    """
    #------------

    #-----vinaca-----
    query_vinaca_tongcapphat_DN = """
        SELECT	count(*) 
        FROM CertificateData 
        WHERE cAFingerprint = '5a8c1f27bfd9accbbc3c9455a63620d3bfa6bb5d' 
            AND subjectDN LIKE '%UID=MST:%' 
            AND subjectDN LIKE %s;        
    """

    query_vinaca_tongcapphat_CN = """
        SELECT	count(*) 
        FROM CertificateData 
        WHERE cAFingerprint = '5a8c1f27bfd9accbbc3c9455a63620d3bfa6bb5d' 
            AND (subjectDN LIKE '%UID=CMND:%' OR subjectDN LIKE '%UID=CCCD:%' OR subjectDN LIKE '%UID=HC:%')
            AND subjectDN LIKE %s;     
    """
    #------------
    
    #-----vinaca256-----
    query_vinaca256_tongcapphat_DN = """
        SELECT	count(*) 
        FROM CertificateData INNER JOIN CertReqHistoryData ON CertificateData.fingerprint = CertReqHistoryData.fingerprint
        WHERE CertificateData.cAFingerprint = '46ac271dff8c61317772a6f240854b930d6714e1'
            AND CertReqHistoryData.`timestamp` < 1704042000000
            AND CertificateData.subjectDN LIKE '%UID=MST:%' 
            AND (CertificateData.subjectDN COLLATE UTF8_GENERAL_CI LIKE %s); 
    """

    query_vinaca256_tongthuhoi_DN = """
        SELECT	count(*) 
        FROM CertificateData
        WHERE cAFingerprint = '46ac271dff8c61317772a6f240854b930d6714e1'
            AND revocationDate < 1704042000000
            AND revocationDate <> - 1
            AND STATUS IN ( 40, 60 )
            AND CertificateData.subjectDN LIKE '%UID=MST:%' 
            AND (CertificateData.subjectDN COLLATE UTF8_GENERAL_CI LIKE %s); 
    """

    query_vinaca256_tonghethan_DN = """
        SELECT	count(*) 
        FROM CertificateData
        WHERE cAFingerprint = '46ac271dff8c61317772a6f240854b930d6714e1'
            AND expireDate < 1704042000000
            AND expireDate <> - 1
            AND revocationDate = - 1 
            AND STATUS = 20
            AND CertificateData.subjectDN LIKE '%UID=MST:%' 
            AND (CertificateData.subjectDN COLLATE UTF8_GENERAL_CI LIKE %s); 
    """

    query_vinaca256_tongcapphat_CN = """
        SELECT	count(*) 
        FROM CertificateData INNER JOIN CertReqHistoryData ON CertificateData.fingerprint = CertReqHistoryData.fingerprint
        WHERE CertificateData.cAFingerprint = '46ac271dff8c61317772a6f240854b930d6714e1'
            AND CertReqHistoryData.`timestamp` < 1704042000000
            AND (CertificateData.subjectDN LIKE '%UID=CMND:%' OR CertificateData.subjectDN LIKE '%UID=CCCD:%' OR CertificateData.subjectDN LIKE '%UID=HC:%')
            AND subjectDN LIKE %s;		   
    """

    query_vinaca256_tongthuhoi_CN = """
        SELECT	count(*) 
        FROM CertificateData
        WHERE cAFingerprint = '46ac271dff8c61317772a6f240854b930d6714e1'
            AND revocationDate < 1704042000000
            AND revocationDate <> - 1
            AND STATUS IN ( 40, 60 )
            AND (subjectDN LIKE '%UID=CMND:%' OR subjectDN LIKE '%UID=CCCD:%' OR subjectDN LIKE '%UID=HC:%')
            AND (subjectDN COLLATE UTF8_GENERAL_CI LIKE %s); 	   
    """   

    query_vinaca256_tonghethan_CN = """
        SELECT	count(*) 
        FROM CertificateData
        WHERE cAFingerprint = '46ac271dff8c61317772a6f240854b930d6714e1'
            AND expireDate < 1704042000000
            AND expireDate <> - 1
            AND revocationDate = - 1 
            AND STATUS = 20
            AND (subjectDN LIKE '%UID=CMND:%' OR subjectDN LIKE '%UID=CCCD:%' OR subjectDN LIKE '%UID=HC:%') 
            AND (subjectDN COLLATE UTF8_GENERAL_CI LIKE %s); 	   
    """  
    #------------

    #-----ejbca-----
    query_ejbca_tongcapphat_DN = """
        SELECT	count(*) 
        FROM CertificateData
        WHERE cAFingerprint = '9c9f0ee4744776ecd42628039eea6760e4a6ddb6'
            AND notBefore < 1704042000000
            AND subjectDN LIKE '%UID=MST:%' 
            AND subjectDN LIKE %s;
    """

    query_ejbca_tongcapphat_CN = """
        SELECT	count(*) 
        FROM CertificateData 
        WHERE cAFingerprint = '9c9f0ee4744776ecd42628039eea6760e4a6ddb6' 
            AND notBefore < 1704042000000
            AND (subjectDN LIKE '%UID=CMND:%' OR subjectDN LIKE '%UID=CCCD:%' OR subjectDN LIKE '%UID=HC:%')
            AND subjectDN LIKE %s; 	   
    """
    #------------
    
    try:
        cursor = conn.cursor()
        results = []
        for province in province_data:
            query = """
				SELECT	count(*) 
				FROM CertificateData
				WHERE cAFingerprint = '9c9f0ee4744776ecd42628039eea6760e4a6ddb6'
					AND expireDate < 1704042000000
					AND expireDate <> - 1 
					AND revocationDate = - 1 
					AND STATUS = 20 
					AND (subjectDN LIKE '%UID=CMND:%' OR subjectDN LIKE '%UID=CCCD:%' OR subjectDN LIKE '%UID=HC:%')
					AND subjectDN LIKE %s;
			"""
            cursor.execute(query, (f"%ST={province}%",))    

            result = cursor.fetchone()[0]    
            results.append((province, result))
       
        return results
    finally:
        cursor.close()

def extract_common_name(subject):
    start_index = subject.find("CN=")
    if start_index != -1:
        end_index = subject.find(",", start_index)
        if end_index != -1:
            return subject[start_index + 3:end_index]
    return None

def extract_uid(subject):
    start_index = subject.find("UID=")
    if start_index != -1:
        end_index = subject.find(")", start_index)
        if end_index != -1:
            return subject[start_index + 4:end_index]
    return None

# def check_certificate_status(cert_path, issuer_path, result_text):
#     try:
#         # Load PEM encoded certificate and issuer
#         with open(cert_path, "rb") as cert_file, open(issuer_path, "rb") as issuer_file:
#             pem_cert = cert_file.read()
#             pem_issuer = issuer_file.read()

#         cert = load_pem_x509_certificate(pem_cert)
#         issuer = load_pem_x509_certificate(pem_issuer)

#         # Function to extract OCSP server URL from certificate
#         def get_ocsp_server(cert):
#             aia = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
#             ocsps = [ia for ia in aia if ia.access_method == AuthorityInformationAccessOID.OCSP]
#             if not ocsps:
#                 raise Exception('No OCSP server entry in AIA')
#             return ocsps[0].access_location.value

#         # Create OCSP request
#         # builder = ocsp.OCSPRequestBuilder().add_certificate(cert, issuer, SHA256())
#         builder = ocsp.OCSPRequestBuilder().add_certificate(cert, issuer, SHA1())
#         req = builder.build()


#         # Get OCSP server URL
#         ocsp_server_url = get_ocsp_server(cert)

#         # Send OCSP request and check response
#         response = requests.post(ocsp_server_url, data=req.public_bytes(Encoding.DER), headers={'Content-Type': 'application/ocsp-request'})
        
#         # Check if the response is successful (status code 200)
#         if response.status_code == 200:
#             result_str = ""
#             # Load the DER encoded OCSP response
#             ocsp_resp = ocsp.load_der_ocsp_response(response.content)
#             # Access the response status
#             result_str += "----- OCSP Responder -----"
#             if ocsp_resp.response_status == OCSPResponseStatus.SUCCESSFUL:
#                 cert_status = ocsp_resp.certificate_status
#                 cert_status_name = cert_status.name
#                 result_str += f"\nCertificate Status: {cert_status_name}"
#                 if isinstance(cert_status, OCSPCertStatus):
#                     cert_status_name = cert_status.name
#                     if cert_status_name == "REVOKED":
#                         revocation_time = ocsp_resp.revocation_time                        
#                         result_str += f"\nRevocation Time: {revocation_time}"
#                 else:
#                     cert_status_name = str(cert_status)
#             this_update_gmt7 = ocsp_resp.this_update + timedelta(hours=7)
#             result_str +=  f"\nThis Update: {this_update_gmt7}"                    
#             result_str +=  f"\nOCSP URI: {ocsp_server_url}"
#             result_str += "\n\n----- Certificate Infomation -----"
#             subject = str(cert.subject)
#             result_str += f"\nSubject: {extract_common_name(subject)}"
#             result_str += f"\n{extract_uid(subject)}"
#             result_str += f"\nSerial Number: {decimal_to_hex(cert.serial_number)}"
#             result_str += f"\nValid from: {cert.not_valid_before_utc.strftime('%Y-%m-%d %H:%M:%S')}"
#             result_str += f"\nValid to: {cert.not_valid_after_utc.strftime('%Y-%m-%d %H:%M:%S')}"

#             result_text.config(state=tk.NORMAL)
#             result_text.delete(1.0, tk.END)
#             result_text.insert(tk.END, result_str)
#             result_text.config(state=tk.DISABLED) 
#         else:
#             messagebox.showinfo(f"Failed to get OCSP response. Status code: {response.status_code}")          
#     except Exception as e:
#         print("An error occurred:", e)

def check_certificate_status(cert_path, issuer_path, result_text):
    try:
        # Load PEM encoded certificate and issuer using context managers
        with open(cert_path, "rb") as cert_file, open(issuer_path, "rb") as issuer_file:
            pem_cert = cert_file.read()
            pem_issuer = issuer_file.read()

        cert = load_pem_x509_certificate(pem_cert)
        issuer = load_pem_x509_certificate(pem_issuer)

        # Function to extract OCSP server URL from certificate
        def get_ocsp_server(cert):
            try:
                aia = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
                ocsps = [ia for ia in aia if ia.access_method == AuthorityInformationAccessOID.OCSP]
                if not ocsps:
                    raise ValueError('No OCSP server entry in AIA')
                return ocsps[0].access_location.value
            except Exception as e:
                raise ValueError(f"Failed to extract OCSP URL: {e}")

        # Create OCSP request using SHA256 for better security (updated from SHA1)
        builder = OCSPRequestBuilder().add_certificate(cert, issuer, hashes.SHA256())
        req = builder.build()

        # Get OCSP server URL
        ocsp_server_url = get_ocsp_server(cert)

        # Send OCSP request with timeout for better reliability
        response = requests.post(
            ocsp_server_url,
            data=req.public_bytes(serialization.Encoding.DER),
            headers={'Content-Type': 'application/ocsp-request'},
            timeout=10  # Add timeout to prevent hanging
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get OCSP response. Status code: {response.status_code}")

        ocsp_resp = load_der_ocsp_response(response.content)

        # Build result string more efficiently using a list and join
        result_lines = []

        result_lines.append("----- OCSP Responder -----")
        result_lines.append(f"Response Status: {ocsp_resp.response_status.name}")

        if ocsp_resp.response_status == OCSPResponseStatus.SUCCESSFUL:
            # Certificate Status
            cert_status = ocsp_resp.certificate_status.name
            result_lines.append(f"Certificate Status: {cert_status}")

            if ocsp_resp.certificate_status == OCSPCertStatus.REVOKED:
                # Sử dụng revocation_time_utc để tránh deprecation warning và thêm timezone offset
                timezone_offset = timedelta(hours=7)
                revocation_time = ocsp_resp.revocation_time_utc + timezone_offset
                result_lines.append(f"Revocation Time: {revocation_time.strftime('%Y-%m-%d %H:%M:%S')}")
                if ocsp_resp.revocation_reason is not None:
                    result_lines.append(f"Revocation Reason: {ocsp_resp.revocation_reason.name}")

            # Time adjustments (assuming +7 hours for timezone, make configurable if needed)
            timezone_offset = timedelta(hours=7)
            this_update = ocsp_resp.this_update_utc + timezone_offset
            result_lines.append(f"This Update: {this_update.strftime('%Y-%m-%d %H:%M:%S')}")
            if ocsp_resp.next_update_utc:
                next_update = ocsp_resp.next_update_utc + timezone_offset
                result_lines.append(f"Next Update: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
            if ocsp_resp.produced_at_utc:
                produced_at = ocsp_resp.produced_at_utc + timezone_offset
                result_lines.append(f"Produced At: {produced_at.strftime('%Y-%m-%d %H:%M:%S')}")

            # Responder info
            if ocsp_resp.responder_name:
                result_lines.append(f"Responder Name: {str(ocsp_resp.responder_name)}")
            if ocsp_resp.responder_key_hash:
                result_lines.append(f"Responder Key Hash: {ocsp_resp.responder_key_hash.hex()}")

            # Signature Algorithm
            if ocsp_resp.signature_algorithm_oid:
                result_lines.append(f"Signature Algorithm: {ocsp_resp.signature_algorithm_oid._name}")

            # Verify OCSP signature with dynamic padding based on algorithm
            try:
                responder_certs = ocsp_resp.certificates
                signer_cert = None
                if responder_certs:
                    # Select the first cert with OCSP Signing EKU
                    for candidate in responder_certs:
                        try:
                            eku = candidate.extensions.get_extension_for_oid(ExtensionOID.EXTENDED_KEY_USAGE).value
                            if ExtendedKeyUsageOID.OCSP_SIGNING in eku:
                                signer_cert = candidate
                                break
                        except Exception:
                            continue

                # Fallback to issuer if no suitable responder cert found
                if signer_cert is None:
                    signer_cert = issuer

                # Determine padding based on signature algorithm
                if ocsp_resp.signature_algorithm_oid == oid.SignatureAlgorithmOID.RSASSA_PSS:
                    padding = asymmetric_padding.PSS(
                        mgf=asymmetric_padding.MGF1(ocsp_resp.signature_hash_algorithm),
                        salt_length=asymmetric_padding.PSS.MAX_LENGTH
                    )
                    msg = "Padding scheme: RSASSA-PSS"
                else:
                    padding = asymmetric_padding.PKCS1v15()
                    msg = "Padding scheme: PKCS#1 v1.5"

                print(msg)   
                # Verify signature
                signer_cert.public_key().verify(
                    ocsp_resp.signature,
                    ocsp_resp.tbs_response_bytes,
                    padding,
                    ocsp_resp.signature_hash_algorithm
                )
                result_lines.append("Signature Verification: OK ✅")
            except Exception as e:
                result_lines.append(f"Signature Verification: FAILED ❌ ({e})")

            # OCSP URI
            result_lines.append(f"OCSP URI: {ocsp_server_url}")

        # Certificate Information
        result_lines.append("\n----- Certificate Information -----")
        subject = str(cert.subject)
        result_lines.append(f"Subject: {extract_common_name(subject)}") 
        result_lines.append(extract_uid(subject))  
        result_lines.append(f"Serial Number: {decimal_to_hex(cert.serial_number)}")  
        result_lines.append(f"Valid from: {cert.not_valid_before_utc.strftime('%Y-%m-%d %H:%M:%S')}")
        result_lines.append(f"Valid to: {cert.not_valid_after_utc.strftime('%Y-%m-%d %H:%M:%S')}")

        # Show on GUI
        result_str = "\n".join(result_lines)
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, result_str)
        result_text.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")



def open_folder(folder_name):
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    
    target_folder = os.path.join(current_dir, folder_name)

    if os.path.exists(target_folder):
        if sys.platform == "win32":
            os.startfile(target_folder)
        elif sys.platform == "darwin":
            os.system(f"open {target_folder}")
        else:
            os.system(f"xdg-open {target_folder}")
    else:
        print(f"Folder '{folder_name}' không tồn tại.")


# def open_log_in_notepad(section_name):
#     current_date = datetime.now().date()
#     current_directory = os.path.dirname(os.path.abspath(__file__))
#     log_file_path = os.path.join(current_directory, "log", f"{current_date}.{section_name}.log")
#     notepad_plus_plus_path = r"C:\Program Files\Notepad++\notepad++.exe"

#     try:
#         subprocess.Popen([notepad_plus_plus_path, log_file_path])
#     except Exception as e:
#         print("Không thể mở file log bằng Notepad:", e)


# def open_log_in_notepad(section_name):
#     current_date = datetime.now().date()
    
#     if getattr(sys, 'frozen', False):
#         current_directory = os.path.dirname(sys.executable)
#     else:
#         current_directory = os.path.dirname(os.path.abspath(__file__))

#     log_file_path = os.path.join(current_directory, "log", f"{current_date}.{section_name}.log")
#     notepad_plus_plus_path = r"C:\Program Files\Notepad++\notepad++.exe"
#     default_notepad_path = r"notepad.exe"

#     try:
#         if os.path.exists(notepad_plus_plus_path):
#             subprocess.Popen([notepad_plus_plus_path, log_file_path])
#         else:
#             subprocess.Popen([default_notepad_path, log_file_path])
#     except Exception as e:
#         print("Không thể mở file log bằng Notepad hoặc Notepad++:", e)

def open_log_in_notepad(section_name, base_log_dir="log"):
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")

    # Tạo đường dẫn thư mục và file log
    if getattr(sys, 'frozen', False):
        current_directory = os.path.dirname(sys.executable)
    else:
        current_directory = os.path.dirname(os.path.abspath(__file__))

    log_file_path = os.path.join(current_directory, base_log_dir, year, month, f"{section_name}.log")

    # Kiểm tra tồn tại file log
    if not os.path.exists(log_file_path):
        print(f"Không tìm thấy file log: {log_file_path}")
        return

    # Đường dẫn Notepad++ và Notepad mặc định
    notepad_plus_plus_path = r"C:\Program Files\Notepad++\notepad++.exe"
    default_notepad_path = r"notepad.exe"

    try:
        if os.path.exists(notepad_plus_plus_path):
            subprocess.Popen([notepad_plus_plus_path, log_file_path])
        else:
            subprocess.Popen([default_notepad_path, log_file_path])
    except Exception as e:
        print("Không thể mở file log bằng Notepad hoặc Notepad++:", e)


