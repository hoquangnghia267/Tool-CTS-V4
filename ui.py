import tkinter as tk 

def create_root():
    root = tk.Tk()
    root.title("Thiết lập kết nối database")
    root.configure(background='#66ff70')  # Thiết lập màu nền cho cửa sổ
    return root

# def create_frame(root):
#     frame = tk.Frame(root, padx=20, pady=20, bg='#2ecc71')  # Đặt padding và màu nền cho frame
#     frame.pack()
#     return frame

def create_frame(root):

    frame = tk.Frame(root, padx=50, pady=50, bg='#66ff70')  # Đặt padding và màu nền cho frame
    frame.pack()
    return frame

def center_window(window, width, height):
    # Lấy kích thước màn hình
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Tính toán vị trí giữa màn hình
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    # Đặt kích thước và vị trí cho cửa sổ
    window.geometry(f'{width}x{height}+{x}+{y}')