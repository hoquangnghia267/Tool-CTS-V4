import datetime
from datetime import datetime, timezone, timedelta
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
from functions import (check_certificate_status, convert_timestamp_to_gmt7, decimal_to_hex, export_base64_certificates, get_text_data, get_text_single, note_hotro_tms1, query_info_cts, update_revoked_list, update_revoked_list_new, update_revoked_list_force,
                       block_tms1, block_tms2, unblock_tms1, unblock_tms2, notifications_tms2, off_notifications_tms1, off_notifications_tms2, 
                       search_certificates_by_subject, query_cts_theo_tinh, notifications_tms1, get_info_TMS1, get_info_TMS2, update_unrevoked_list, hex_to_decimal)
from tkinter import filedialog

# Các hàm chức năng của ứng dụng


def show_connection(section_name):
    messagebox.showinfo("Infomation", f"Your connection: {section_name}")


def open_check_certificate_status(parent):
    update_window = tk.Toplevel(parent)
    update_window.title("Check OCSP")
    update_window.grab_set()


    def select_cert_file():
        cert_path = filedialog.askopenfilename()
        cert_path_label.config(text=cert_path)

    def select_issuer_file():
        issuer_path = filedialog.askopenfilename()
        issuer_path_label.config(text=issuer_path)

    def check():
        cert_path = cert_path_label.cget("text")
        issuer_path = issuer_path_label.cget("text")
        check_certificate_status(cert_path, issuer_path, get_result_text)

    cert_path_label = tk.Label(update_window, text="Cert Path:")
    cert_path_label.grid(row=0, column=0, padx=10)

    cert_path_button = tk.Button(update_window, text="Choose Cert File", command=select_cert_file)
    cert_path_button.grid(row=1, column=0, padx=10)

    issuer_path_label = tk.Label(update_window, text="Issuer Path:")
    issuer_path_label.grid(row=2, column=0, padx=10)

    issuer_path_button = tk.Button(update_window, text="Choose Issuer File", command=select_issuer_file)
    issuer_path_button.grid(row=3, column=0, padx=10)

    global get_result_text
    get_result_text = tk.Text(update_window, height=20, width=100, state=tk.DISABLED, font=("Helvetica", 13), spacing1=3, spacing2=3, spacing3=3)
    get_result_text.grid(row=5, column=0, padx=20, pady=20)

    check_button = tk.Button(update_window, text="CHECK OCSP", command=check)
    check_button.grid(row=4, column=0, pady=10)

#-------------------------------------------------------------

#----CTS-----
# def open_get_serial_from_taxcode(parent, conn):
#     update_window = tk.Toplevel(parent)
#     update_window.title("Get Serial Number")

#     # Tạo các thành phần giao diện
#     #1 lable idtoken
#     taxcode_label = tk.Label(update_window, text="Enter Tax code:")
#     taxcode_label.grid(row=0, column=0, padx=10)

#     taxcode_text = tk.Text(update_window, width=15, height=1)
#     taxcode_text.grid(row=1, column=0, padx=10)

#     update_button = tk.Button(update_window, text="Search", command=lambda: get_serial_from_taxcode(conn, get_text_single(taxcode_text), get_result_text))
#     update_button.grid(row=2, column=0, pady=10)

#     global get_result_text
#     get_result_text = tk.Text(update_window, height=15, width=60, state=tk.DISABLED, font=("Helvetica", 10), spacing1=3, spacing2=3, spacing3=3)
#     get_result_text.grid(row=3, column=0, padx=10, pady=10)


def open_get_serial_from_taxcode(parent, conn, section_name):
    """
    Opens a window to search for certificates.
    The view is conditional based on the section_name.
    """
    search_window = tk.Toplevel(parent)
    search_window.title("Certificate Search")
    
    # --- Center The Window ---
    parent.update_idletasks()
    window_width = 1500
    window_height = 900
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    position_x = int(parent_x + (parent_width / 2) - (window_width / 2))
    position_y = int(parent_y + (parent_height / 2) - (window_height / 2))
    search_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    is_extended_view = section_name in ["localejbca", "CAv7"]

    # --- Search Input ---
    search_label = tk.Label(search_window, text="Enter tax code or certificate information:", font=("Helvetica", 12))
    search_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
    search_input = tk.Text(search_window, width=40, height=1, font=("Helvetica", 12))
    search_input.grid(row=1, column=0, padx=10, pady=5, sticky="w")

    # --- Conditional Date Filter ---
    if is_extended_view:
        date_filter_frame = tk.Frame(search_window)
        date_filter_frame.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        tk.Label(date_filter_frame, text="Filter by 'Valid from' date:", font=("Helvetica", 12)).grid(row=0, column=0, columnspan=4)
        
        tk.Label(date_filter_frame, text="From:", font=("Helvetica", 10)).grid(row=1, column=0, padx=(0, 5))
        from_date_entry = tk.Entry(date_filter_frame, width=12, font=("Helvetica", 10))
        from_date_entry.grid(row=1, column=1, padx=(0, 10))

        tk.Label(date_filter_frame, text="To:", font=("Helvetica", 10)).grid(row=1, column=2, padx=(0, 5))
        to_date_entry = tk.Entry(date_filter_frame, width=12, font=("Helvetica", 10))
        to_date_entry.grid(row=1, column=3, padx=(0, 10))
        
        tk.Label(date_filter_frame, text="Format: YYYY-MM-DD", font=("Helvetica", 8, "italic")).grid(row=2, column=0, columnspan=4, pady=(5,0))

    # --- Search Button ---
    search_button_row = 3 if is_extended_view else 2
    search_button = tk.Button(search_window, text="Search", font=("Helvetica", 12, "bold"), width=12, command=lambda: do_search())
    search_button.grid(row=search_button_row, column=0, pady=10)

    # --- Results Table ---
    table_row = 4 if is_extended_view else 3
    frame_table = tk.Frame(search_window)
    frame_table.grid(row=table_row, column=0, padx=10, pady=10, sticky="nsew")
    search_window.grid_rowconfigure(table_row, weight=1)
    search_window.grid_columnconfigure(0, weight=1)

    if is_extended_view:
        columns = ("Serial Number", "Valid from", "Valid to", "Status", "Username", "SubjectDN")
    else:
        columns = ("Serial Number", "Expire Date", "Status", "Username", "SubjectDN")
    
    scrollbar_y = ttk.Scrollbar(frame_table, orient="vertical")
    scrollbar_x = ttk.Scrollbar(frame_table, orient="horizontal")
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=25,
                        yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    scrollbar_y.config(command=tree.yview)
    scrollbar_x.config(command=tree.xview)
    tree.grid(row=0, column=0, sticky='nsew')
    scrollbar_y.grid(row=0, column=1, sticky='ns')
    scrollbar_x.grid(row=1, column=0, sticky='ew')
    frame_table.grid_rowconfigure(0, weight=1)
    frame_table.grid_columnconfigure(0, weight=1)
    
    tree.column("Serial Number", width=250, anchor="w")
    if is_extended_view:
        tree.column("Valid from", width=150, anchor="w")
        tree.column("Valid to", width=150, anchor="w")
    else:
        tree.column("Expire Date", width=150, anchor="w")
    tree.column("Status", width=80, anchor="w")
    tree.column("Username", width=200, anchor="w")
    tree.column("SubjectDN", width=1000, anchor="w")

    sort_state = {col: False for col in columns}

    def sort_column(col):
        data = [(tree.set(item, col), item) for item in tree.get_children("")]
        data.sort(reverse=sort_state[col])
        for index, (_, item) in enumerate(data):
            tree.move(item, "", index)
        sort_state[col] = not sort_state[col]

    for col in columns:
        tree.heading(col, text=col, anchor="w", command=lambda c=col: sort_column(c))

    def do_search():
        """Performs the search and displays results in the Treeview."""
        tree.delete(*tree.get_children())
        search_term = get_text_single(search_input)
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return

        start_date = None
        end_date = None
        if is_extended_view:
            start_date = from_date_entry.get()
            end_date = to_date_entry.get()
            # Basic validation for date format
            try:
                if start_date: datetime.strptime(start_date, '%Y-%m-%d')
                if end_date: datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Invalid Date", "Date format must be YYYY-MM-DD.")
                return

        results = search_certificates_by_subject(conn, search_term, section_name, start_date, end_date)

        if not results:
            messagebox.showinfo("Information", "No matching data found.")
            return

        for row in results:
            serial_hex = decimal_to_hex(row[0])
            expire_date_gmt7 = convert_timestamp_to_gmt7(row[1])
            status = row[2]
            username = row[3]
            subject_dn = row[4]
            
            if is_extended_view:
                valid_from_gmt7 = convert_timestamp_to_gmt7(row[5])
                values = (serial_hex, valid_from_gmt7, expire_date_gmt7, status, username, subject_dn)
            else:
                values = (serial_hex, expire_date_gmt7, status, username, subject_dn)
            
            tree.insert("", tk.END, values=values)

    def copy_serial_keyboard(event=None):
        selected_items = tree.selection()
        if selected_items:
            serials_to_copy = []
            for item_id in selected_items:
                serial_number = tree.item(item_id, "values")[0]
                serials_to_copy.append(serial_number)
            if serials_to_copy:
                clipboard_content = "\n".join(serials_to_copy)
                search_window.clipboard_clear()
                search_window.clipboard_append(clipboard_content)
                search_window.update()

    search_window.bind("<Return>", lambda event: do_search())
    search_window.bind("<Control-c>", copy_serial_keyboard)



def open_query_cts_theo_tinh(parent, conn):
    def show_results():
        province_data = province_text.get("1.0", "end-1c").split("\n")
        results = query_cts_theo_tinh(conn, province_data)
        result_text.delete("1.0", tk.END)  # Xóa bất kỳ nội dung cũ nào trên ô kết quả
        for result in results:
            result_text.insert(tk.END, f"{result}\n")

    # Tạo cửa sổ
    update_window = tk.Toplevel(parent)
    update_window.title("Kiểm tra thông tin CTS theo tỉnh thành.")

    # Tạo các thành phần giao diện
    province_label = tk.Label(update_window, text="Tên tỉnh thành")
    province_label.grid(row=0, column=0, padx=10)

    province_text = tk.Text(update_window, width=40, height=40)
    province_text.grid(row=1, column=0, padx=10)

    query_button = tk.Button(update_window, text="Truy vấn", command=show_results)
    query_button.grid(row=2, column=0, pady=10)

    result_label = tk.Label(update_window, text="Kết quả:")
    result_label.grid(row=0, column=1, padx=10, pady=(0, 5))

    result_text = tk.Text(update_window, width=40, height=40)
    result_text.grid(row=1, column=1, padx=10)

def open_query_list_serial(parent, conn):

    def fetch_data():
        input_data = input_text.get("1.0", tk.END).strip()
        serial_numbers = input_data.split('\n')
        
        # Chuyển đổi các giá trị hex sang decimal
        decimal_serials = [hex_to_decimal(sn) for sn in serial_numbers]

        results = query_info_cts(conn, decimal_serials)
        
        if results:
            output_text.delete('1.0', tk.END)
            
            found_serials = {str(row[0]) for row in results}  # Tạo tập hợp các serial number tìm thấy
            
            for row in results:
                serial_hex = decimal_to_hex(row[0])
                expire_date = row[3]
                revoke_date = row[2]
                subject_DN = row[4]
                username = row[5]
                expire_date_gmt7 = convert_timestamp_to_gmt7(expire_date)

                #output_text.insert(tk.END, f"SerialNumber: {serial_hex} - SubjectDN: {subject_DN}\n")
                #output_text.insert(tk.END, f"SerialNumber: {serial_hex} - Status: {row[1]} - ExpireDate: {expire_date_gmt7} - RevocationDate: {revoke_date}\n")
                output_text.insert(tk.END, f"SerialNumber: {serial_hex} - Status: {row[1]} - SubjectDN: {subject_DN} - Username: {username}\n")
                #output_text.insert(tk.END, f"SerialNumber: {serial_hex} - Status: {row[1]} - ExpireDate: {expire_date_gmt7}\n")  

            # Tìm các serial number không có trong kết quả
            not_found_serials = [sn for sn in serial_numbers if str(hex_to_decimal(sn)) not in found_serials]
            
            if not_found_serials:
                output_text.insert(tk.END, "\nSerials not found in database:\n")
                for sn in not_found_serials:
                    output_text.insert(tk.END, f"{sn}\n")
        else:
            messagebox.showinfo("No Results", "No data found for the provided serial numbers.")



    # Tạo giao diện Tkinter
    update_window = tk.Toplevel(parent)
    update_window.title("Database Query.")

    tk.Label(update_window, text="Enter Serial Numbers (hex, one per line):").pack()

    input_text = scrolledtext.ScrolledText(update_window, width=40, height=20)
    input_text.pack(padx=10, pady=10)

    tk.Button(update_window, text="Fetch Data", command=fetch_data).pack()

    tk.Label(update_window, text="Results:").pack()

    output_text = scrolledtext.ScrolledText(update_window, width=200, height=30)
    output_text.pack(padx=10, pady=10)


def open_convert_timestamp(parent):
    def convert_timestamp():
        # Lấy tất cả các dòng từ ô nhập liệu
        timestamps = timestamp_text.get("1.0", "end-1c").strip().split("\n")
        result_text.delete("1.0", tk.END)
        
        for timestamp in timestamps:
            try:
                # Chuyển đổi từng timestamp thành datetime
                timestamp = int(timestamp.strip())
                dt = datetime.fromtimestamp(timestamp / 1000.0, timezone.utc)
                # Chuyển đổi sang GMT+7
                dt_gmt7 = dt + timedelta(hours=7)
                # Hiển thị kết quả
                result_text.insert(tk.END, f"{dt_gmt7.strftime('%Y-%m-%d %H:%M:%S')}\n")
            except ValueError:
                result_text.insert(tk.END, f"{timestamp} -> Vui lòng nhập một timestamp hợp lệ.\n")

    # Tạo cửa sổ
    converter_window = tk.Toplevel(parent)
    converter_window.title("Chuyển đổi Timestamp thành ngày GMT+7")

    # Tạo các thành phần giao diện
    timestamp_label = tk.Label(converter_window, text="Nhập Timestamp (mỗi dòng một timestamp):")
    timestamp_label.grid(row=0, column=0, padx=10, pady=5)

    timestamp_text = tk.Text(converter_window, width=40, height=20)
    timestamp_text.grid(row=1, column=0, padx=10, pady=5)

    convert_button = tk.Button(converter_window, text="Chuyển đổi", command=convert_timestamp)
    convert_button.grid(row=2, columnspan=2, pady=10)

    result_label = tk.Label(converter_window, text="Kết quả:")
    result_label.grid(row=0, column=1, padx=10, pady=(0, 5))

    result_text = tk.Text(converter_window, width=40, height=20)
    result_text.grid(row=1, column=1, padx=10, pady=5)

def open_hsm_admin(parent):
    update_window = tk.Toplevel(parent)
    update_window.title("HSM Administrator")

    # Tạo các thành phần giao diện
    hsm_label = tk.Label(update_window, text="HSM Administrator Tool")
    hsm_label.grid(row=0, column=0, padx=10, pady=10)

    hsm_info = tk.Label(update_window, text="This is a placeholder for HSM administration functionalities.")
    hsm_info.grid(row=1, column=0, padx=10, pady=10)


def open_revoke_list(parent, conn, logger):
    # Tạo cửa sổ cập nhật
    update_window = tk.Toplevel(parent)
    update_window.title("Update Revoked Data")

    # Tạo các thành phần giao diện
    serial_label = tk.Label(update_window, text="Serial Numbers:")
    serial_label.grid(row=0, column=0, padx=10)

    revocation_label = tk.Label(update_window, text="Revocation Dates:")
    revocation_label.grid(row=0, column=1, padx=10)

    serial_text = tk.Text(update_window, width=40, height=30)
    serial_text.grid(row=1, column=0, padx=10)

    revocation_text = tk.Text(update_window, width=20, height=30)
    revocation_text.grid(row=1, column=1, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: update_revoked_list(conn, get_text_data(serial_text), get_text_data(revocation_text), logger))
    update_button.grid(row=2, columnspan=2, pady=10)

def open_revoke_list_force(parent, conn, logger):
    # Tạo cửa sổ cập nhật
    update_window = tk.Toplevel(parent)
    update_window.title("Update Revoked Data")

    # Tạo các thành phần giao diện
    serial_label = tk.Label(update_window, text="Serial Numbers:")
    serial_label.grid(row=0, column=0, padx=10)

    revocation_label = tk.Label(update_window, text="Revocation Dates:")
    revocation_label.grid(row=0, column=1, padx=10)

    serial_text = tk.Text(update_window, width=40, height=30)
    serial_text.grid(row=1, column=0, padx=10)

    revocation_text = tk.Text(update_window, width=20, height=30)
    revocation_text.grid(row=1, column=1, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: update_revoked_list_force(conn, get_text_data(serial_text), get_text_data(revocation_text), logger))
    update_button.grid(row=2, columnspan=2, pady=10)




def open_unrevoke_list(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Update Unrevoked Data")

    # Tạo các thành phần giao diện
    serial_label = tk.Label(update_window, text="Serial Numbers:")
    serial_label.grid(row=0, column=0, padx=10)

    serial_text = tk.Text(update_window, width=40, height=30)
    serial_text.grid(row=1, column=0, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: update_unrevoked_list(conn, get_text_data(serial_text), logger))
    update_button.grid(row=2, columnspan=2, pady=10)

def open_export_base64_certificates(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Export multiple certificates")

    # Tạo các thành phần giao diện
    serial_label = tk.Label(update_window, text="Serial Numbers:")
    serial_label.grid(row=0, column=0, padx=10)

    serial_text = scrolledtext.ScrolledText(update_window, width=40, height=30)
    serial_text.grid(row=1, column=0, padx=10)

    update_button = tk.Button(update_window, text="Export", command=lambda: export_base64_certificates(conn, get_text_data(serial_text), logger))
    update_button.grid(row=2, columnspan=2, pady=10)


def open_revoke_list_just_a_revokedate(parent, conn, logger):
    # Tạo cửa sổ cập nhật
    update_window = tk.Toplevel(parent)
    update_window.title("Update Revoked Data")

    # Tạo các thành phần giao diện
    serial_label = tk.Label(update_window, text="Serial Numbers:")
    serial_label.grid(row=0, column=0, padx=10)

    revocation_label = tk.Label(update_window, text="Revocation Dates:")
    revocation_label.grid(row=0, column=1, padx=10)

    serial_text = tk.Text(update_window, width=40, height=30)
    serial_text.grid(row=1, column=0, padx=10)

    revocation_text = tk.Text(update_window, width=20, height=1)
    revocation_text.grid(row=1, column=1, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: update_revoked_list_new(conn, get_text_data(serial_text), get_text_single(revocation_text), logger))
    update_button.grid(row=2, columnspan=2, pady=10)


#-------------------------------------------------------------

#-----TMS1-----
def open_get_info_TMS1(parent, conn):
    update_window = tk.Toplevel(parent)
    update_window.title("Kiểm tra thông tin TMS1")

    # Tạo các thành phần giao diện
    #1 lable idtoken
    id_label = tk.Label(update_window, text="Enter Token ID:")
    id_label.grid(row=0, column=0, padx=10)

    token_text = tk.Text(update_window, width=20, height=1)
    token_text.grid(row=1, column=0, padx=10)

    update_button = tk.Button(update_window, text="Search", command=lambda: get_info_TMS1(conn, get_text_single(token_text), get_result_text))
    update_button.grid(row=2, column=0, pady=10)

    #global get_result_text
#    get_result_text = tk.Text(update_window, height=15, width=80, state=tk.DISABLED, font=("Helvetica", 10), spacing1=3, spacing2=3, spacing3=3)
    get_result_text = scrolledtext.ScrolledText(update_window, height=15, width=80, state=tk.DISABLED, font=("Helvetica", 10), spacing1=3, spacing2=3, spacing3=3)
    get_result_text.grid(row=3, column=0, padx=10, pady=10)

#note_hotro_tms1
def open_note_hotro_tms1(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("ON note TMS1 on page hotro.smartsign.com.vn")

    # Tạo các thành phần giao diện
    #2 lable Content
    content_label = tk.Label(update_window, text="Enter The Note Content")
    content_label.grid(row=0, column=0, padx=10)

    content_text = tk.Text(update_window, width=60, height=5)
    content_text.grid(row=1, column=0, padx=10)

    #3 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token List")
    idtoken_label.grid(row=2, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=20, height=30)
    idtoken_text.grid(row=3, column=0, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: note_hotro_tms1(conn, get_text_data(idtoken_text), get_text_single(content_text), logger))
    update_button.grid(row=4, column=0, pady=20)


def open_notifications_tms1(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("ON Notifications TMS1")

    # Tạo các thành phần giao diện
    #2 lable Content
    content_label = tk.Label(update_window, text="Enter The Notification Content")
    content_label.grid(row=0, column=0, padx=10)

    content_text = tk.Text(update_window, width=60, height=5)
    content_text.grid(row=1, column=0, padx=10)

    #3 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token List")
    idtoken_label.grid(row=2, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=20, height=30)
    idtoken_text.grid(row=3, column=0, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: notifications_tms1(conn, get_text_data(idtoken_text), get_text_single(content_text), logger))
    update_button.grid(row=4, column=0, pady=20)

def open_notifications_tms1_off(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Off TMS1 notifications")

    # Tạo các thành phần giao diện
    #1 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token:")
    idtoken_label.grid(row=0, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=30, height=40)
    idtoken_text.grid(row=1, column=0, padx=20)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: off_notifications_tms1(conn, get_text_data(idtoken_text), logger))
    update_button.grid(row=2, column=0, pady=20)
   
def open_block_tms1(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Update Block TMS1")

    # Tạo các thành phần giao diện
    #1 lable block_note
    block_note_label = tk.Label(update_window, text="Enter the token block notice")
    block_note_label.grid(row=0, column=0, padx=10)

    block_note_text = tk.Text(update_window, width=50, height=5)
    block_note_text.grid(row=1, column=0, padx=10)

    #2 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token:")
    idtoken_label.grid(row=2, column=0, padx=10)

    idtoken_text =scrolledtext.ScrolledText(update_window, width=20, height=40)
    idtoken_text.grid(row=3, column=0, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: block_tms1(conn, get_text_data(idtoken_text), get_text_single(block_note_text), logger))
    update_button.grid(row=4, column=0, pady=20)

def open_unblock_tms1(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Update Unblock TMS1")

    # Tạo các thành phần giao diện
    #1 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token:")
    idtoken_label.grid(row=0, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=30, height=40)
    idtoken_text.grid(row=1, column=0, padx=20)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: unblock_tms1(conn, get_text_data(idtoken_text), logger))
    update_button.grid(row=2, column=0, pady=20)

#-----TMS2----get_info_TMS2
def open_get_info_TMS2(parent, conn):
    update_window = tk.Toplevel(parent)
    update_window.title("Kiểm tra thông tin TMS2")

    # Tạo các thành phần giao diện
    #1 lable idtoken
    id_label = tk.Label(update_window, text="Enter Token ID:")
    id_label.grid(row=0, column=0, padx=10)

    token_text = tk.Text(update_window, width=20, height=1)
    token_text.grid(row=1, column=0, padx=10)

    update_button = tk.Button(update_window, text="Search", command=lambda: get_info_TMS2(conn, get_text_single(token_text), get_result_text))
    update_button.grid(row=2, column=0, pady=10)

    #global get_result_text
    get_result_text = tk.Text(update_window, height=15, width=80, state=tk.DISABLED, font=("Helvetica", 10), spacing1=3, spacing2=3, spacing3=3)
    get_result_text.grid(row=3, column=0, padx=10, pady=10)

def open_block_tms2(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Update Block TMS2")

    # Tạo các thành phần giao diện
    #1 lable block_note
    block_note_label = tk.Label(update_window, text="Enter the token block notice")
    block_note_label.grid(row=0, column=0, padx=10)

    block_note_text = tk.Text(update_window, width=50, height=5)
    block_note_text.grid(row=1, column=0, padx=10)

    #2 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token:")
    idtoken_label.grid(row=2, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=20, height=40)
    idtoken_text.grid(row=3, column=0, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: block_tms2(conn, get_text_data(idtoken_text), get_text_single(block_note_text), logger))
    update_button.grid(row=4, column=0, pady=20)

def open_unblock_tms2(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Update Unblock TMS2")

    # Tạo các thành phần giao diện
    #1 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token:")
    idtoken_label.grid(row=0, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=30, height=40)
    idtoken_text.grid(row=1, column=0, padx=20)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: unblock_tms2(conn, get_text_data(idtoken_text), logger))
    update_button.grid(row=2, column=0, pady=20)

def open_notifications_tms2(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Update Notifications TMS2")

    # Tạo các thành phần giao diện
    #1 lable Title
    title_label = tk.Label(update_window, text="Enter The Notification Title")
    title_label.grid(row=0, column=0, padx=10)

    title_text = tk.Text(update_window, width=30, height=2)
    title_text.grid(row=1, column=0, padx=10)

    #2 lable Content
    content_label = tk.Label(update_window, text="Enter The Notification Content \n(Current notice end date: 2025-05-19 23:59:59)")
    content_label.grid(row=2, column=0, padx=10)

    content_text = tk.Text(update_window, width=60, height=5)
    content_text.grid(row=3, column=0, padx=10)

    #3 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token List")
    idtoken_label.grid(row=4, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=20, height=30)
    idtoken_text.grid(row=5, column=0, padx=10)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: notifications_tms2(conn, get_text_data(idtoken_text), get_text_single(title_text), get_text_single(content_text), logger))
    update_button.grid(row=6, column=0, pady=20)

def open_off_notifications_tms2(parent, conn, logger):
    update_window = tk.Toplevel(parent)
    update_window.title("Off TMS2 notifications")

    # Tạo các thành phần giao diện
    #1 lable idtoken
    idtoken_label = tk.Label(update_window, text="ID Token:")
    idtoken_label.grid(row=0, column=0, padx=10)

    idtoken_text = scrolledtext.ScrolledText(update_window, width=30, height=40)
    idtoken_text.grid(row=1, column=0, padx=20)

    update_button = tk.Button(update_window, text="Update Records", command=lambda: off_notifications_tms2(conn, get_text_data(idtoken_text), logger))
    update_button.grid(row=2, column=0, pady=20)



