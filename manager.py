

import tkinter as tk
from tkinter import ttk
from gui import (open_check_certificate_status, open_convert_timestamp, open_export_base64_certificates, open_get_info_TMS2, open_note_hotro_tms1, open_off_notifications_tms2, open_query_list_serial, 
                 open_revoke_list_just_a_revokedate, show_connection, open_block_tms2, 
                 open_get_serial_from_taxcode, open_notifications_tms1, 
                 open_block_tms1, open_notifications_tms1_off, 
                 open_notifications_tms2, open_hsm_admin,
                 open_query_cts_theo_tinh, open_revoke_list, open_revoke_list_force,
                 open_unblock_tms1, open_unblock_tms2, open_unrevoke_list, 
                 open_get_info_TMS1)
from functions import (open_folder, open_log_in_notepad, query_database, revoke_certificate_update, setup_logging, 
                       unrevoke_certificate_update, export_base64_cert)
from database import get_database_config, connect_to_database
from ui import center_window, create_frame
from PIL import Image, ImageTk


# def get_section_name(root, section_name_entry):
#     section_name = section_name_entry.get()
#     database_config = get_database_config(section_name)
#     conn = connect_to_database(database_config)
#     root.destroy()
#     setup_logging(section_name)
#     create_gui(section_name, conn)


def get_section_name(root, section_name_entry):
    section_name = section_name_entry.get()
    database_config = get_database_config(section_name)
    conn = connect_to_database(database_config)
    root.destroy()
    create_gui(section_name, conn)

def open_connect():
    root = tk.Tk()
    root.title("Connecting...")
 
    def on_enter(event=None):
        get_section_name(root, section_name_entry)

    # Tạo frame chứa label và entry
    frame = create_frame(root)

    section_name_label = tk.Label(frame, text="Enter System", font=('Helvetica', 14), bg=frame.cget('bg'))
    section_name_label.grid(row=0, column=0, pady=10)

    section_name_entry = tk.Entry(frame, width=20, font=('Helvetica', 14))
    section_name_entry.grid(row=1, column=0)
    section_name_entry.bind('<Return>', on_enter)

    connect_button = tk.Button(frame, text="Connect", command=on_enter, font=('Helvetica', 12))
    connect_button.grid(row=2, column=0, pady=20)

    root.mainloop()

def open_connect_2(root, logger):
    logger.handlers.clear()
    root.destroy()
    open_connect()


def create_gui(section_name, conn):
        
    logger = setup_logging(section_name)
    
    root = tk.Tk()
    root.title("My Application")

    # Create frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)
    window_width = 750
    window_height = 500
    # root.geometry(f"{window_width}x{window_height}")
    center_window(root, window_width, window_height)

    # Create menu
    menu = tk.Menu(root)
    root.config(menu=menu)

    # create menu "File"
    file_menu = tk.Menu(menu)
    menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Infomation", command=lambda: show_connection(section_name))
    file_menu.add_command(label="Reset connection", command=lambda: open_connect_2(root, logger))


    # TMS1
    TMS1_menu = tk.Menu(menu)
    menu.add_cascade(label="TMS1", menu=TMS1_menu)
    TMS1_menu.add_command(label="Infomation token", command=lambda: open_get_info_TMS1(root, conn))
    TMS1_menu.add_command(label="Run notes on hotro.smartsign.com.vn", command=lambda: open_note_hotro_tms1(root, conn, logger))
    TMS1_menu.add_command(label="ON notifications", command=lambda: open_notifications_tms1(root, conn, logger))
    TMS1_menu.add_command(label="OFF notifications", command=lambda: open_notifications_tms1_off(root, conn, logger))
    TMS1_menu.add_command(label="Block TMS1", command=lambda: open_block_tms1(root, conn, logger))
    TMS1_menu.add_command(label="Unblock TMS1", command=lambda: open_unblock_tms1(root, conn, logger))

    # Tạo menu "TMS2"
    TMS2_menu = tk.Menu(menu)
    menu.add_cascade(label="TMS2", menu=TMS2_menu)
    TMS2_menu.add_command(label="Infomation token", command=lambda: open_get_info_TMS2(root, conn))
    TMS2_menu.add_command(label="ON notifications", command=lambda: open_notifications_tms2(root, conn, logger))
    TMS2_menu.add_command(label="OFF notifications", command=lambda: open_off_notifications_tms2(root, conn, logger))
    TMS2_menu.add_command(label="Block token-TMS2", command=lambda: open_block_tms2(root, conn, logger))
    TMS2_menu.add_command(label="Unblock token-TMS2", command=lambda: open_unblock_tms2(root, conn, logger))


    # Menu "Cert"
    cert_menu = tk.Menu(menu)
    menu.add_cascade(label="Certficates", menu=cert_menu)
    cert_menu.add_command(label="Revoke list 1 (By Serial)", command=lambda: open_revoke_list(root, conn, logger))
    cert_menu.add_command(label="Revoke list 1 (By Serial - Force)", command=lambda: open_revoke_list_force(root, conn, logger))
    cert_menu.add_command(label="Revoke list 2 (Unified)", command=lambda: open_revoke_list_just_a_revokedate(root, conn, logger))
    cert_menu.add_command(label="Unrevoke list", command=lambda: open_unrevoke_list(root, conn, logger))
    cert_menu.add_command(label="Export multi Certificates", command=lambda: open_export_base64_certificates(root, conn, logger))
   
    # Menu "Reports"
    repo_menu = tk.Menu(menu)
    menu.add_cascade(label="Reports", menu=repo_menu)
    repo_menu.add_command(label="Export reports by province", command=lambda: open_query_cts_theo_tinh(root, conn))
    repo_menu.add_command(label="Export Information CTS", command=lambda: open_query_list_serial(root, conn))
    #open_query_list_serial
     

    # Menu "View"
    view_menu = tk.Menu(menu)
    menu.add_cascade(label="View", menu=view_menu)
    view_menu.add_command(label="View Log File", command=lambda: open_log_in_notepad(section_name))      
    view_menu.add_command(label="View Log Folder ", command=lambda: open_folder("log"))
    view_menu.add_command(label="View Certificates Folder ", command=lambda: open_folder("Certificates"))

  # Menu "Convert"
    conv_menu = tk.Menu(menu)
    menu.add_cascade(label="Convert", menu=conv_menu)
    conv_menu.add_command(label="Convert Timestamp", command=lambda: open_convert_timestamp(root))      
#   conv_menu.add_command(label="Convert Hex to Dec", command=open_convert_Hex-to-Dec)

    # Menu "HSM"
    hsm_menu = tk.Menu(menu)
    menu.add_cascade(label="HSM", menu=hsm_menu)
    view_menu.add_command(label="HSM Administrator", command=lambda: open_hsm_admin(root))      
    # view_menu.add_command(label="View Log Folder ", command=lambda: open_folder("log"))
    # view_menu.add_command(label="View Certificates Folder ", command=lambda: open_folder("Certificates"))


    # Create a PanedWindow containing both columns
    paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=5, sashrelief=tk.RAISED)
    paned_window.pack(fill=tk.BOTH, expand=True)

    # Left column
    menu_frame = tk.Frame(paned_window, width=window_width * 0.3)
    menu_frame.pack_propagate(False)  # Do not allow frames to change size based on content

    # Add menu_frame to PanedWindow first
    paned_window.add(menu_frame)

    check_ocsp_button = tk.Button(menu_frame, text="Check OCSP", command=lambda: open_check_certificate_status(root))
    check_ocsp_button.pack(side=tk.TOP, fill=tk.X)

    search_serial_button = tk.Button(menu_frame, text="Certificate Search", command=lambda: open_get_serial_from_taxcode(root, conn, section_name))
    search_serial_button.pack(side=tk.TOP, fill=tk.X)

    search_multiple_cert = tk.Button(menu_frame, text="Check multiple certificates", command=lambda: open_query_list_serial(root, conn))
    search_multiple_cert.pack(side=tk.TOP, fill=tk.X)

    # Right column
    content_frame = tk.Frame(paned_window, width=window_width * 0.7)
    paned_window.add(content_frame)

    # Creates a PanedWindow containing two rows of the right column
    paned_content = tk.PanedWindow(content_frame, orient=tk.VERTICAL, sashwidth=5, sashrelief=tk.RAISED)
    paned_content.pack(fill=tk.BOTH, expand=True)

    # Upper row of right column (30%)
    upper_frame = tk.Frame(paned_content, height=window_height * 0.3)
    upper_frame.pack_propagate(False)  # Do not allow frames to change size based on content
    paned_content.add(upper_frame)

    # Create label "Enter serialNumber:"
    serial_label = tk.Label(upper_frame, text="Enter Serial Number")
    serial_label.pack(side=tk.TOP, padx=5)

    # Create serialNumber input box
    serial_entry = tk.Entry(upper_frame, width=40)
    serial_entry.pack(side=tk.TOP)

    # Add tick mark (checkbox)
    chk_revoke_date = tk.BooleanVar()
    chk_revoke = tk.Checkbutton(upper_frame, text="Select Revoke Date", variable=chk_revoke_date)
    chk_revoke.pack()
    # Widget allows users to enter revoke date
    entry_revoke_date = tk.Entry(upper_frame)
    entry_revoke_date.pack()

    # Create a container to hold 4 nodes
    button_container = tk.Frame(upper_frame)
    button_container.pack(side=tk.TOP, pady=10)

    # Create a button that performs a function depending on the menu selection
    execute_button = tk.Button(button_container, text="Execute", command=lambda: query_database(conn, serial_entry, result_text))
    execute_button.pack(side=tk.LEFT, padx=5)

    unrevoke_button = tk.Button(button_container, text="Unrevoke", command=lambda: unrevoke_certificate_update(conn, serial_entry, section_name, logger))
    unrevoke_button.pack(side=tk.LEFT, padx=5)

    revoke_button = tk.Button(button_container, text="Revoke", command=lambda: revoke_certificate_update(conn, serial_entry, chk_revoke_date, entry_revoke_date, section_name, logger))
    revoke_button.pack(side=tk.LEFT, padx=5)

    export_button = tk.Button(button_container, text="Export", command=lambda: export_base64_cert(conn, serial_entry))
    export_button.pack(side=tk.LEFT, padx=5)

    # Bottom row of right column (70%)
    lower_frame = tk.Frame(paned_content, height=window_height * 0.7)
    lower_frame.pack_propagate(False)  # Do not allow frames to change size based on content
    paned_content.add(lower_frame)

    # Create result cell
    result_text = tk.Text(lower_frame, height=10, width=70, state=tk.DISABLED, font=("Helvetica", 10), spacing1=3, spacing2=3, spacing3=3)
    result_text.pack(side=tk.TOP, pady=15)

    device_frame = tk.Frame(lower_frame)
    device_frame.pack(side=tk.BOTTOM)
    label_text = f"Connection: {section_name}"
    label = tk.Label(device_frame, text=label_text, font=("Helvetica", 12, "bold"), fg="red")
    label.pack(pady=10)  # The distance between the label and the bottom edge of the frame

    #-------------------------------------------------------------------------------------------------------------------
    # Launch the application
    root.mainloop()
