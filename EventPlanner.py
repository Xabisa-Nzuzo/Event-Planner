from logging import root
import sys
# try to start a virtual display if pyvirtualdisplay is installed
try:
    from pyvirtualdisplay import Display
    display = Display(visible=0, size=(1024, 768))
    display.start()
except Exception:
    display = None

# try importing tkinter and exit with instructions if it's missing
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
except ModuleNotFoundError as e:
    print("Module 'tkinter' not found. Install system tk package (Ubuntu) and retry:")
    print("  sudo apt update && sudo apt install -y python3-tk xvfb")
    print("Install pyvirtualdisplay into your venv if you want automatic virtual X:")
    print("  /workspaces/Event-Planner/.venv/bin/python -m pip install pyvirtualdisplay")
    if display:
        display.stop()
    sys.exit(1)

import sqlite3
import hashlib
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re

class EventPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Event Planner Application")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Database setup
        self.setup_database()
        
        # Current user
        self.current_user = None
        
        # GUI setup
        self.setup_gui()
        
        # Show login frame initially
        self.show_login_frame()
    
    def setup_database(self):
        """Initialize the SQLite database and create necessary tables"""
        self.conn = sqlite3.connect('event_planner.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Events table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                password TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Guests table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (event_id) REFERENCES events (id)
            )
        ''')
        
        self.conn.commit()
    
    def setup_gui(self):
        """Set up the main GUI components"""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Login frame
        self.login_frame = ttk.Frame(self.main_frame)
        
        # Registration frame
        self.registration_frame = ttk.Frame(self.main_frame)
        
        # Dashboard frame
        self.dashboard_frame = ttk.Frame(self.main_frame)
        
        # Event management frame
        self.event_frame = ttk.Frame(self.main_frame)
        
        # Guest management frame
        self.guest_frame = ttk.Frame(self.main_frame)
    
    def show_login_frame(self):
        """Display the login interface"""
        self.clear_main_frame()
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self.login_frame, text="Event Planner Login", font=('Arial', 16)).pack(pady=20)
        
        # Username
        ttk.Label(self.login_frame, text="Username:").pack(pady=5)
        self.login_username = ttk.Entry(self.login_frame, width=30)
        self.login_username.pack(pady=5)
        
        # Password
        ttk.Label(self.login_frame, text="Password:").pack(pady=5)
        self.login_password = ttk.Entry(self.login_frame, width=30, show="*")
        self.login_password.pack(pady=5)
        
        # Login button
        ttk.Button(self.login_frame, text="Login", command=self.login).pack(pady=10)
        
        # Register link
        ttk.Button(self.login_frame, text="Don't have an account? Register here", 
                  command=self.show_registration_frame).pack(pady=5)
    
    def show_registration_frame(self):
        """Display the registration interface"""
        self.clear_main_frame()
        self.registration_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self.registration_frame, text="Create New Account", font=('Arial', 16)).pack(pady=20)
        
        # Username
        ttk.Label(self.registration_frame, text="Username:").pack(pady=5)
        self.reg_username = ttk.Entry(self.registration_frame, width=30)
        self.reg_username.pack(pady=5)
        
        # Email
        ttk.Label(self.registration_frame, text="Email:").pack(pady=5)
        self.reg_email = ttk.Entry(self.registration_frame, width=30)
        self.reg_email.pack(pady=5)
        
        # Password
        ttk.Label(self.registration_frame, text="Password:").pack(pady=5)
        self.reg_password = ttk.Entry(self.registration_frame, width=30, show="*")
        self.reg_password.pack(pady=5)
        
        # Confirm Password
        ttk.Label(self.registration_frame, text="Confirm Password:").pack(pady=5)
        self.reg_confirm_password = ttk.Entry(self.registration_frame, width=30, show="*")
        self.reg_confirm_password.pack(pady=5)
        
        # Register button
        ttk.Button(self.registration_frame, text="Register", command=self.register).pack(pady=10)
        
        # Back to login
        ttk.Button(self.registration_frame, text="Back to Login", 
                  command=self.show_login_frame).pack(pady=5)
    
    def show_dashboard(self):
        """Display the main dashboard after login"""
        self.clear_main_frame()
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        ttk.Label(self.dashboard_frame, text=f"Welcome, {self.current_user}!", 
                 font=('Arial', 16)).pack(pady=20)
        
        # Buttons for different functionalities
        ttk.Button(self.dashboard_frame, text="Create New Event", 
                  command=self.show_event_creation).pack(pady=10)
        
        ttk.Button(self.dashboard_frame, text="View My Events", 
                  command=self.show_events_list).pack(pady=10)
        
        ttk.Button(self.dashboard_frame, text="Logout", 
                  command=self.logout).pack(pady=10)
    
    def show_event_creation(self, event_id=None):
        """Display the event creation/editing interface"""
        self.clear_main_frame()
        self.event_frame.pack(fill=tk.BOTH, expand=True)
        
        # Check if we're editing an existing event
        editing = event_id is not None
        event_data = None
        
        if editing:
            self.cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            event_data = self.cursor.fetchone()
        
        ttk.Label(self.event_frame, text="Create New Event" if not editing else "Edit Event", 
                 font=('Arial', 16)).pack(pady=20)
        
        # Event name
        ttk.Label(self.event_frame, text="Event Name:").pack(pady=5)
        self.event_name = ttk.Entry(self.event_frame, width=40)
        if editing:
            self.event_name.insert(0, event_data[2])
        self.event_name.pack(pady=5)
        
        # Event date
        ttk.Label(self.event_frame, text="Event Date (YYYY-MM-DD):").pack(pady=5)
        self.event_date = ttk.Entry(self.event_frame, width=40)
        if editing:
            self.event_date.insert(0, event_data[3])
        self.event_date.pack(pady=5)
        
        # Event location
        ttk.Label(self.event_frame, text="Event Location:").pack(pady=5)
        self.event_location = ttk.Entry(self.event_frame, width=40)
        if editing:
            self.event_location.insert(0, event_data[4])
        self.event_location.pack(pady=5)
        
        # Event description
        ttk.Label(self.event_frame, text="Event Description:").pack(pady=5)
        self.event_description = tk.Text(self.event_frame, width=40, height=5)
        if editing:
            self.event_description.insert("1.0", event_data[5])
        self.event_description.pack(pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.event_frame)
        button_frame.pack(pady=10)
        
        if editing:
            ttk.Button(button_frame, text="Update Event", 
                      command=lambda: self.save_event(event_id)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Manage Guests", 
                      command=lambda: self.show_guest_management(event_id)).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(button_frame, text="Create Event", 
                      command=self.save_event).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Back to Dashboard", 
                  command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def show_events_list(self):
        """Display a list of the user's events"""
        self.clear_main_frame()
        events_frame = ttk.Frame(self.main_frame)
        events_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(events_frame, text="My Events", font=('Arial', 16)).pack(pady=20)
        
        # Get user's events
        self.cursor.execute("SELECT * FROM events WHERE user_id = (SELECT id FROM users WHERE username = ?)", 
                           (self.current_user,))
        events = self.cursor.fetchall()
        
        if not events:
            ttk.Label(events_frame, text="You haven't created any events yet.").pack(pady=10)
            ttk.Button(events_frame, text="Back to Dashboard", 
                      command=self.show_dashboard).pack(pady=10)
            return
        
        # Create a treeview to display events
        tree_frame = ttk.Frame(events_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        events_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, 
                                  columns=("ID", "Name", "Date", "Location"), show="headings")
        events_tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll.config(command=events_tree.yview)
        
        events_tree.heading("ID", text="ID")
        events_tree.heading("Name", text="Event Name")
        events_tree.heading("Date", text="Date")
        events_tree.heading("Location", text="Location")
        
        events_tree.column("ID", width=50)
        events_tree.column("Name", width=200)
        events_tree.column("Date", width=100)
        events_tree.column("Location", width=150)
        
        for event in events:
            events_tree.insert("", tk.END, values=event[:5])
        
        # Buttons for event actions
        button_frame = ttk.Frame(events_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Edit Selected", 
                  command=lambda: self.edit_selected_event(events_tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Delete Selected", 
                  command=lambda: self.delete_selected_event(events_tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Manage Guests", 
                  command=lambda: self.manage_guests_for_selected(events_tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Back to Dashboard", 
                  command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def show_guest_management(self, event_id):
        """Display the guest management interface for a specific event"""
        self.clear_main_frame()
        self.guest_frame.pack(fill=tk.BOTH, expand=True)
        
        # Get event details
        self.cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        event = self.cursor.fetchone()
        
        ttk.Label(self.guest_frame, text=f"Manage Guests for: {event[2]}", 
                 font=('Arial', 16)).pack(pady=20)
        
        # Add guest section
        add_guest_frame = ttk.LabelFrame(self.guest_frame, text="Add New Guest", padding=10)
        add_guest_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(add_guest_frame, text="Guest Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.guest_name = ttk.Entry(add_guest_frame, width=30)
        self.guest_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_guest_frame, text="Guest Email:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.guest_email = ttk.Entry(add_guest_frame, width=30)
        self.guest_email.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(add_guest_frame, text="Add Guest", 
                  command=lambda: self.add_guest(event_id)).grid(row=2, column=1, padx=5, pady=5, sticky=tk.E)
        
        # Guest list
        guest_list_frame = ttk.LabelFrame(self.guest_frame, text="Guest List", padding=10)
        guest_list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create a treeview to display guests
        tree_scroll = ttk.Scrollbar(guest_list_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        guests_tree = ttk.Treeview(guest_list_frame, yscrollcommand=tree_scroll.set, 
                                  columns=("ID", "Name", "Email", "Status"), show="headings")
        guests_tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll.config(command=guests_tree.yview)
        
        guests_tree.heading("ID", text="ID")
        guests_tree.heading("Name", text="Name")
        guests_tree.heading("Email", text="Email")
        guests_tree.heading("Status", text="Status")
        
        guests_tree.column("ID", width=50)
        guests_tree.column("Name", width=150)
        guests_tree.column("Email", width=200)
        guests_tree.column("Status", width=100)
        
        # Get guests for this event
        self.cursor.execute("SELECT * FROM guests WHERE event_id = ?", (event_id,))
        guests = self.cursor.fetchall()
        
        for guest in guests:
            guests_tree.insert("", tk.END, values=guest)
        
        # Buttons for guest actions
        button_frame = ttk.Frame(self.guest_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Send Invitations", 
                  command=lambda: self.send_invitations(event_id)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Remove Selected", 
                  command=lambda: self.remove_selected_guest(guests_tree, event_id)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Back to Event", 
                  command=lambda: self.show_event_creation(event_id)).pack(side=tk.LEFT, padx=5)
    
    def clear_main_frame(self):
        """Clear all frames from the main frame"""
        for frame in [self.login_frame, self.registration_frame, 
                     self.dashboard_frame, self.event_frame, self.guest_frame]:
            frame.pack_forget()
    
    def hash_password(self, password):
        """Hash a password for storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_password(self):
        """Generate a strong, unique password for events"""
        length = 12
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(characters) for _ in range(length))
        return password
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def register(self):
        """Handle user registration"""
        username = self.reg_username.get()
        email = self.reg_email.get()
        password = self.reg_password.get()
        confirm_password = self.reg_confirm_password.get()
        
        # Validation
        if not username or not email or not password:
            messagebox.showerror("Error", "All fields are required")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if not self.validate_email(email):
            messagebox.showerror("Error", "Invalid email format")
            return
        
        # Check if username or email already exists
        self.cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Username or email already exists")
            return
        
        # Hash password and save user
        hashed_password = self.hash_password(password)
        try:
            self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                               (username, email, hashed_password))
            self.conn.commit()
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login_frame()
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
    
    def login(self):
        """Handle user login"""
        username = self.login_username.get()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        hashed_password = self.hash_password(password)
        
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                           (username, hashed_password))
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = username
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def logout(self):
        """Handle user logout"""
        self.current_user = None
        self.show_login_frame()
    
    def save_event(self, event_id=None):
        """Save or update an event"""
        name = self.event_name.get()
        date = self.event_date.get()
        location = self.event_location.get()
        description = self.event_description.get("1.0", tk.END).strip()
        
        # Validation
        if not name or not date or not location:
            messagebox.showerror("Error", "Event name, date, and location are required")
            return
        
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
            return
        
        # Get user ID
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (self.current_user,))
        user_id = self.cursor.fetchone()[0]
        
        if event_id:  # Update existing event
            try:
                self.cursor.execute(
                    "UPDATE events SET name = ?, date = ?, location = ?, description = ? WHERE id = ?",
                    (name, date, location, description, event_id)
                )
                self.conn.commit()
                messagebox.showinfo("Success", "Event updated successfully!")
                self.show_events_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update event: {str(e)}")
        else:  # Create new event
            # Generate unique password for the event
            event_password = self.generate_password()
            
            try:
                self.cursor.execute(
                    "INSERT INTO events (user_id, name, date, location, description, password) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, name, date, location, description, event_password)
                )
                self.conn.commit()
                messagebox.showinfo("Success", f"Event created successfully!\nEvent Password: {event_password}")
                self.show_events_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create event: {str(e)}")
    
    def edit_selected_event(self, events_tree):
        """Edit the selected event"""
        selection = events_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to edit")
            return
        
        event_id = events_tree.item(selection[0])['values'][0]
        self.show_event_creation(event_id)
    
    def delete_selected_event(self, events_tree):
        """Delete the selected event"""
        selection = events_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to delete")
            return
        
        event_id = events_tree.item(selection[0])['values'][0]
        event_name = events_tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{event_name}'?"):
            try:
                # First delete all guests for this event
                self.cursor.execute("DELETE FROM guests WHERE event_id = ?", (event_id,))
                # Then delete the event
                self.cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
                self.conn.commit()
                messagebox.showinfo("Success", "Event deleted successfully!")
                self.show_events_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete event: {str(e)}")
    
    def manage_guests_for_selected(self, events_tree):
        """Manage guests for the selected event"""
        selection = events_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to manage guests")
            return
        
        event_id = events_tree.item(selection[0])['values'][0]
        self.show_guest_management(event_id)
    
    def add_guest(self, event_id):
        """Add a guest to an event"""
        name = self.guest_name.get()
        email = self.guest_email.get()
        
        if not name or not email:
            messagebox.showerror("Error", "Guest name and email are required")
            return
        
        if not self.validate_email(email):
            messagebox.showerror("Error", "Invalid email format")
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO guests (event_id, name, email) VALUES (?, ?, ?)",
                (event_id, name, email)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Guest added successfully!")
            self.guest_name.delete(0, tk.END)
            self.guest_email.delete(0, tk.END)
            # Refresh guest list
            self.show_guest_management(event_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add guest: {str(e)}")
    
    def remove_selected_guest(self, guests_tree, event_id):
        """Remove the selected guest"""
        selection = guests_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a guest to remove")
            return
        
        guest_id = guests_tree.item(selection[0])['values'][0]
        guest_name = guests_tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to remove '{guest_name}'?"):
            try:
                self.cursor.execute("DELETE FROM guests WHERE id = ?", (guest_id,))
                self.conn.commit()
                messagebox.showinfo("Success", "Guest removed successfully!")
                self.show_guest_management(event_id)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove guest: {str(e)}")
    
    def send_invitations(self, event_id):
        """Send invitation emails to all guests for an event"""
        # Get event details
        self.cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        event = self.cursor.fetchone()
        
        # Get all guests for this event
        self.cursor.execute("SELECT * FROM guests WHERE event_id = ?", (event_id,))
        guests = self.cursor.fetchall()
        
        if not guests:
            messagebox.showwarning("Warning", "No guests to send invitations to")
            return
        
        # For a real implementation, you would need to configure SMTP settings
        # This is a simplified version that shows how it would work
        try:
            # In a real application, you would:
            # 1. Set up SMTP server connection
            # 2. Create email content with event details and unique access link
            # 3. Send to each guest
            
            # For demonstration, we'll just show a success message
            messagebox.showinfo("Success", 
                               f"Invitations sent to {len(guests)} guests for '{event[2]}'!")
            
            # Update guest status to "Invited"
            for guest in guests:
                self.cursor.execute(
                    "UPDATE guests SET status = 'Invited' WHERE id = ?", 
                    (guest[0],)
                )
            self.conn.commit()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send invitations: {str(e)}")
 
def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = EventPlannerApp(root)
    try:
        root.mainloop()
    finally:
        try:
            root.destroy()
        except Exception:
            pass
        if display:
            display.stop()

if __name__ == "__main__":
    main()

root.destroy()

display.stop()