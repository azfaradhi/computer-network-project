import tkinter as tk
from tkinter import scrolledtext, colorchooser, ttk
import threading
import time
from datetime import datetime
from lib.MessageInfo import MessageInfo
import hashlib


class ChatGUI:
    def __init__(self, client):
        self.client = client
        self.user_colors = {}
        self.running = True
        
        # Quick chat templates
        self.quick_chats = [
            "HALOOO",
            "Pesanan sesuai aplikasi?",
            "HIDUPP JO..",
            "Su..suki desu >_<",
            "Konichiwa",
            "Yes!",
        ]
    

        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title(f"GoChat - {self.client.username}")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        # Configure style for ttk widgets
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TButton', 
                       background='#3498db', 
                       foreground='white',
                       padding=5)
        style.map('Custom.TButton',
                 background=[('active', '#2980b9')])

        self.create_header()
        self.create_main_content()
        self.create_input_area()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_messages, daemon=True)
        self.update_thread.start()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_header(self):
        """Create header with title and controls"""
        header_frame = tk.Frame(self.root, bg='#34495e', height=60)
        header_frame.pack(fill='x', padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, 
                              text=f"Chatroom - {self.client.username}", 
                              font=('Arial', 16, 'bold'),
                              bg='#34495e', 
                              fg='white')
        title_label.pack(side='left', padx=20, pady=15)
        
        # Controls frame
        controls_frame = tk.Frame(header_frame, bg='#34495e')
        controls_frame.pack(side='right', padx=20, pady=10)
        
        # Background color button
        self.color_button = ttk.Button(controls_frame, 
                                      text="Background", 
                                      command=self.change_background_color,
                                      style='Custom.TButton')
        self.color_button.pack(side='right', padx=5)
        
        # Online users counter (placeholder)
        users_label = tk.Label(controls_frame, 
                              text="Online", 
                              font=('Arial', 10),
                              bg='#34495e', 
                              fg='#95a5a6')
        users_label.pack(side='right', padx=15)

    def create_main_content(self):
        """Create main content area with chat and sidebar"""
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Chat area (left side)
        chat_frame = tk.Frame(main_frame, bg='#2c3e50')
        chat_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Chat display with custom styling
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, 
            wrap=tk.WORD, 
            state='disabled', 
            width=60, 
            height=25,
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Consolas', 11),
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill='both', expand=True)
        
        # Sidebar (right side)
        self.create_sidebar(main_frame)

    def create_sidebar(self, parent):
        """Create sidebar with quick emotes and quick chat"""
        sidebar_frame = tk.Frame(parent, bg='#34495e', width=200)
        sidebar_frame.pack(side='right', fill='y')
        sidebar_frame.pack_propagate(False)
        
        
        # Separator
        separator = tk.Frame(sidebar_frame, height=2, bg='#95a5a6')
        separator.pack(fill='x', padx=20, pady=10)
        
        # Quick Chat Section
        quick_chat_label = tk.Label(sidebar_frame, 
                                   text="Quick Chat", 
                                   font=('Arial', 12, 'bold'),
                                   bg='#34495e', 
                                   fg='white')
        quick_chat_label.pack(pady=(10, 10))
        
        # Quick chat scrollable frame
        chat_canvas = tk.Canvas(sidebar_frame, bg='#34495e', highlightthickness=0)
        chat_scrollbar = ttk.Scrollbar(sidebar_frame, orient="vertical", command=chat_canvas.yview)
        chat_scrollable_frame = tk.Frame(chat_canvas, bg='#34495e')
        
        chat_scrollable_frame.bind(
            "<Configure>",
            lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
        )
        
        chat_canvas.create_window((0, 0), window=chat_scrollable_frame, anchor="nw")
        chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
        
        chat_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        chat_scrollbar.pack(side="right", fill="y")
        
        # Quick chat buttons
        for chat in self.quick_chats:
            btn = tk.Button(chat_scrollable_frame, 
                           text=chat, 
                           width=22,
                           font=('Arial', 9),
                           bg='#27ae60',
                           fg='white',
                           border=0,
                           activebackground='#229954',
                           wraplength=150,
                           justify='center',
                           command=lambda c=chat: self.send_quick_chat(c))
            btn.pack(pady=2, padx=5, fill='x')

    def create_input_area(self):
        """Create input area with enhanced styling"""
        input_frame = tk.Frame(self.root, bg='#34495e', height=80)
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        input_frame.pack_propagate(False)
        
        # Input container
        input_container = tk.Frame(input_frame, bg='#34495e')
        input_container.pack(expand=True, fill='both', padx=20, pady=15)
        
        # Entry field with modern styling
        self.entry = tk.Entry(input_container, 
                             font=('Arial', 12),
                             bg='white',
                             fg='#2c3e50',
                             borderwidth=0,
                             highlightthickness=2,
                             highlightcolor='#3498db',
                             insertbackground='#2c3e50')
        self.entry.pack(side='left', fill='both', expand=True, ipady=8)
        self.entry.bind("<Return>", self.send_message)
        
        # Send button
        send_button = tk.Button(input_container, 
                               text="Send", 
                               font=('Arial', 11, 'bold'),
                               bg='#e74c3c',
                               fg='white',
                               border=0,
                               activebackground='#c0392b',
                               padx=20,
                               command=self.send_message)
        send_button.pack(side='right', padx=(10, 0), ipady=8)
        
        # Placeholder text functionality
        self.entry.config(fg='#95a5a6')
        self.entry.bind('<FocusIn>', self.on_entry_focus_in)
        self.entry.bind('<FocusOut>', self.on_entry_focus_out)

    def on_entry_focus_in(self, event):
        if self.entry.get() == ".":
            self.entry.delete(0, tk.END)
            self.entry.config(fg='#2c3e50')

    def on_entry_focus_out(self, event):
        if not self.entry.get():
            self.entry.insert(0, "")
            self.entry.config(fg='#95a5a6')

    def insert_emote(self, emote):
        """Insert emote into the entry field"""
        current_pos = self.entry.index(tk.INSERT)
        current_text = self.entry.get()
        
        # Clear placeholder if present
        if current_text == "":
            self.entry.delete(0, tk.END)
            self.entry.config(fg='#2c3e50')
            current_text = ""
            current_pos = 0
        
        # Insert emote
        self.entry.insert(current_pos, emote)
        self.entry.focus()

    def send_quick_chat(self, message):
        """Send a quick chat message"""
        self.client.send_broadcast_message(message)

    def change_background_color(self):
        """Show color picker for background"""
        color = colorchooser.askcolor(title="Choose Chat Background Color")
        if color[1]:
            self.chat_display.configure(bg=color[1])

    def send_message(self, event=None):
        """Send message from entry field"""
        message = self.entry.get().strip()
        if message and message != "":
            self.client.send_broadcast_message(message)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, "")
            self.entry.config(fg='#95a5a6')

    def get_user_color(self, username):
        """Generate consistent color for each user"""
        if username not in self.user_colors:
            hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
            r = (hash_val >> 16) & 0xFF
            g = (hash_val >> 8) & 0xFF
            b = hash_val & 0xFF
            
            # Ensure good contrast
            if r + g + b < 300:
                r = min(255, r + 100)
                g = min(255, g + 100)
                b = min(255, b + 100)
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.user_colors[username] = color
        return self.user_colors[username]

    def update_messages(self):
        """Update chat display with new messages"""
        last_len = 0
        while self.running:
            if len(self.client.messages) != last_len:
                last_len = len(self.client.messages)

                self.chat_display.configure(state='normal')
                self.chat_display.delete(1.0, tk.END)

                for msg_info in self.client.messages:
                    timestamp = msg_info.time.strftime("%H:%M:%S")
                    username_color = self.get_user_color(msg_info.username)
                    
                    # Format message with better styling
                    time_text = f"[{timestamp}] "
                    username_text = f"{msg_info.username}: "
                    message_text = f"{msg_info.msg}\n"
                    
                    # Insert timestamp
                    self.chat_display.insert(tk.END, time_text)
                    self.chat_display.tag_add("timestamp", f'end - {len(time_text)}c', f'end - 1c')
                    self.chat_display.tag_config("timestamp", foreground="#95a5a6", font=('Consolas', 9))
                    
                    # Insert username
                    self.chat_display.insert(tk.END, username_text)
                    self.chat_display.tag_add(f"user_{msg_info.username}", f'end - {len(username_text)}c', f'end - 1c')
                    self.chat_display.tag_config(f"user_{msg_info.username}", 
                                               foreground=username_color, 
                                               font=('Consolas', 11, 'bold'))
                    
                    # Insert message
                    self.chat_display.insert(tk.END, message_text)
                    self.chat_display.tag_add("message", f'end - {len(message_text)}c', f'end - 1c')
                    self.chat_display.tag_config("message", foreground="#2c3e50", font=('Consolas', 11))

                self.chat_display.configure(state='disabled')
                self.chat_display.yview(tk.END)

            time.sleep(0.5)  # Reduced sleep time for more responsive updates

    def on_close(self):
        """Handle window close event"""
        self.running = False
        self.client.close_connection(self.client.server_ip, self.client.server_port)
        self.root.destroy()

    def run(self):
        """Start the GUI"""
        self.root.mainloop()