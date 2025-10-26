import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
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
        self.root.configure(bg='#f0f8ff')
        
        # Data storage files
        self.users_file = "users.json"
        self.events_file = "events.json"
        
        # Current user session
        self.current_user = None
        
        # Initialize data files
        self.initialize_data_files()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Show login screen initially
        self.show_login_screen()
    
    def initialize_data_files(self):
        """Initialize JSON files for data storage"""
        for file in [self.users_file, self.events_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump([], f)
    
    def load_data(self, filename):
        """Load data from JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_data(self, filename, data):
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
            return False
    
    def clear_frame(self):
        """Clear all widgets from main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Display login/registration screen"""
        self.clear_frame()
        
        # Title
        title_label = ttk.Label(self.main_frame, text="Event Planner", 
                               font=('Arial', 24, 'bold'), foreground='#2c3e50')
        title_label.pack(pady=20)
        
        # Login Frame
        login_frame = ttk.LabelFrame(self.main_frame, text="Login", padding="20")
        login_frame.pack(pady=20, padx=50, fill=tk.X)
        
        # Username
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Password
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Buttons
        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Login", 
                  command=self.login).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Register", 
                  command=self.register).pack(side=tk.LEFT, padx=10)
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.login())
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def register(self):
        """Handle user registration"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        # Ask for email
        email = simpledialog.askstring("Registration", "Enter your email:")
        if not email:
            return
        
        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return
        
        # Load existing users
        users = self.load_data(self.users_file)
        
        # Check if username already exists
        if any(user['username'] == username for user in users):
            messagebox.showerror("Error", "Username already exists")
            return
        
        # Create new user
        new_user = {
            'username': username,
            'password': password,  # In real app, hash the password
            'email': email
        }
        
        users.append(new_user)
        
        if self.save_data(self.users_file, users):
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
    
    def login(self):
        """Handle user login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        users = self.load_data(self.users_file)
        
        for user in users:
            if user['username'] == username and user['password'] == password:
                self.current_user = user
                self.show_dashboard()
                return
        
        messagebox.showerror("Error", "Invalid username or password")
    
    def generate_password(self, length=12):
        """Generate a strong random password"""
        try:
            characters = string.ascii_letters + string.digits + "!@#$%^&*()"
            password = ''.join(random.choice(characters) for _ in range(length))
            return password
        except Exception as e:
            messagebox.showerror("Error", f"Password generation failed: {str(e)}")
            return "Fallback123!"
    
    def show_dashboard(self):
        """Display main dashboard after login"""
        self.clear_frame()
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(header_frame, text=f"Welcome, {self.current_user['username']}!", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="Logout", 
                  command=self.logout).pack(side=tk.RIGHT)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.main_frame)
        nav_frame.pack(pady=20)
        
        ttk.Button(nav_frame, text="Create Event", 
                  command=self.create_event, width=20).pack(pady=5)
        ttk.Button(nav_frame, text="My Events", 
                  command=self.show_my_events, width=20).pack(pady=5)
        ttk.Button(nav_frame, text="Manage Guests", 
                  command=self.manage_guests, width=20).pack(pady=5)
        
        # Recent events
        self.show_recent_events()
    
    def show_recent_events(self):
        """Display recent events on dashboard"""
        events = self.load_data(self.events_file)
        user_events = [e for e in events if e['creator'] == self.current_user['username']]
        
        if user_events:
            events_frame = ttk.LabelFrame(self.main_frame, text="Recent Events", padding="10")
            events_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Create treeview
            columns = ('Event Name', 'Date', 'Location', 'Guests')
            tree = ttk.Treeview(events_frame, columns=columns, show='headings', height=8)
            
            # Define headings
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Add events
            for event in user_events[-5:]:  # Show last 5 events
                tree.insert('', tk.END, values=(
                    event['name'],
                    event['date'],
                    event['location'],
                    len(event['guests'])
                ))
            
            tree.pack(fill=tk.BOTH, expand=True)
    
    def create_event(self):
        """Create a new event"""
        self.clear_frame()
        
        # Back button
        ttk.Button(self.main_frame, text="← Back to Dashboard", 
                  command=self.show_dashboard).pack(anchor=tk.W, pady=10)
        
        # Event form
        form_frame = ttk.LabelFrame(self.main_frame, text="Create New Event", padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Event name
        ttk.Label(form_frame, text="Event Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(form_frame, width=40)
        name_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Date
        ttk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=5)
        date_entry = ttk.Entry(form_frame, width=40)
        date_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Location
        ttk.Label(form_frame, text="Location:").grid(row=2, column=0, sticky=tk.W, pady=5)
        location_entry = ttk.Entry(form_frame, width=40)
        location_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=5)
        description_text = tk.Text(form_frame, width=40, height=4)
        description_text.grid(row=3, column=1, pady=5, padx=10)
        
        def save_event():
            """Save the new event"""
            try:
                name = name_entry.get().strip()
                date = date_entry.get().strip()
                location = location_entry.get().strip()
                description = description_text.get("1.0", tk.END).strip()
                
                if not all([name, date, location]):
                    messagebox.showerror("Error", "Please fill in all required fields")
                    return
                
                # Validate date format
                try:
                    datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Error", "Please enter date in YYYY-MM-DD format")
                    return
                
                # Generate event password
                event_password = self.generate_password()
                
                # Create event object
                new_event = {
                    'id': len(self.load_data(self.events_file)) + 1,
                    'name': name,
                    'date': date,
                    'location': location,
                    'description': description,
                    'creator': self.current_user['username'],
                    'password': event_password,
                    'guests': [],
                    'created_at': datetime.now().isoformat()
                }
                
                # Save event
                events = self.load_data(self.events_file)
                events.append(new_event)
                
                if self.save_data(self.events_file, events):
                    messagebox.showinfo("Success", 
                                      f"Event created successfully!\nEvent Password: {event_password}")
                    self.show_dashboard()
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create event: {str(e)}")
        
        # Save button
        ttk.Button(form_frame, text="Create Event", 
                  command=save_event).grid(row=4, column=1, sticky=tk.E, pady=15)
    
    def show_my_events(self):
        """Display all events created by the current user"""
        self.clear_frame()
        
        # Back button
        ttk.Button(self.main_frame, text="← Back to Dashboard", 
                  command=self.show_dashboard).pack(anchor=tk.W, pady=10)
        
        events = self.load_data(self.events_file)
        user_events = [e for e in events if e['creator'] == self.current_user['username']]
        
        if not user_events:
            ttk.Label(self.main_frame, text="No events found").pack(pady=50)
            return
        
        # Events list
        events_frame = ttk.LabelFrame(self.main_frame, text="My Events", padding="10")
        events_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(events_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Event Name', 'Date', 'Location', 'Guests', 'Password')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Add events
        for event in user_events:
            tree.insert('', tk.END, values=(
                event['id'],
                event['name'],
                event['date'],
                event['location'],
                len(event['guests']),
                event['password']
            ))
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(events_frame)
        action_frame.pack(pady=10)
        
        ttk.Button(action_frame, text="Edit Event", 
                  command=lambda: self.edit_event(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete Event", 
                  command=lambda: self.delete_event(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="View Guests", 
                  command=lambda: self.view_guests(tree)).pack(side=tk.LEFT, padx=5)
    
    def edit_event(self, tree):
        """Edit selected event"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to edit")
            return
        
        # Implementation for editing event
        messagebox.showinfo("Info", "Edit feature would be implemented here")
    
    def delete_event(self, tree):
        """Delete selected event"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to delete")
            return
        
        event_id = tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this event?"):
            events = self.load_data(self.events_file)
            events = [e for e in events if e['id'] != event_id]
            
            if self.save_data(self.events_file, events):
                messagebox.showinfo("Success", "Event deleted successfully")
                self.show_my_events()
    
    def view_guests(self, tree):
        """View guests for selected event"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to view guests")
            return
        
        event_id = tree.item(selection[0])['values'][0]
        self.manage_event_guests(event_id)
    
    def manage_guests(self):
        """Show interface for managing guests across all events"""
        self.clear_frame()
        
        ttk.Button(self.main_frame, text="← Back to Dashboard", 
                  command=self.show_dashboard).pack(anchor=tk.W, pady=10)
        
        ttk.Label(self.main_frame, text="Select an event to manage guests", 
                 font=('Arial', 12)).pack(pady=10)
        
        events = self.load_data(self.events_file)
        user_events = [e for e in events if e['creator'] == self.current_user['username']]
        
        if not user_events:
            ttk.Label(self.main_frame, text="No events found").pack(pady=50)
            return
        
        for event in user_events:
            event_frame = ttk.Frame(self.main_frame)
            event_frame.pack(fill=tk.X, padx=20, pady=5)
            
            ttk.Label(event_frame, text=f"{event['name']} - {event['date']}").pack(side=tk.LEFT)
            ttk.Button(event_frame, text="Manage Guests", 
                      command=lambda e=event: self.manage_event_guests(e['id'])).pack(side=tk.RIGHT)
    
    def manage_event_guests(self, event_id):
        """Manage guests for a specific event"""
        events = self.load_data(self.events_file)
        event = next((e for e in events if e['id'] == event_id), None)
        
        if not event:
            messagebox.showerror("Error", "Event not found")
            return
        
        self.clear_frame()
        
        # Back button
        ttk.Button(self.main_frame, text="← Back", 
                  command=self.manage_guests).pack(anchor=tk.W, pady=10)
        
        # Event info
        info_frame = ttk.LabelFrame(self.main_frame, text="Event Information", padding="10")
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(info_frame, text=f"Event: {event['name']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Date: {event['date']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Event Password: {event['password']}").pack(anchor=tk.W)
        
        # Guest management
        guest_frame = ttk.LabelFrame(self.main_frame, text="Guest Management", padding="10")
        guest_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Add guest form
        add_frame = ttk.Frame(guest_frame)
        add_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(add_frame, text="Guest Email:").pack(side=tk.LEFT)
        guest_email = ttk.Entry(add_frame, width=30)
        guest_email.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(add_frame, text="Guest Name:").pack(side=tk.LEFT)
        guest_name = ttk.Entry(add_frame, width=20)
        guest_name.pack(side=tk.LEFT, padx=10)
        
        def add_guest():
            """Add a new guest to the event"""
            email = guest_email.get().strip()
            name = guest_name.get().strip()
            
            if not email or not name:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            if not self.validate_email(email):
                messagebox.showerror("Error", "Please enter a valid email address")
                return
            
            # Check if guest already exists
            if any(g['email'] == email for g in event['guests']):
                messagebox.showerror("Error", "Guest with this email already exists")
                return
            
            # Add guest
            event['guests'].append({
                'name': name,
                'email': email,
                'invited_at': datetime.now().isoformat()
            })
            
            # Update events data
            events = self.load_data(self.events_file)
            for e in events:
                if e['id'] == event_id:
                    e['guests'] = event['guests']
                    break
            
            if self.save_data(self.events_file, events):
                messagebox.showinfo("Success", "Guest added successfully")
                guest_email.delete(0, tk.END)
                guest_name.delete(0, tk.END)
                self.manage_event_guests(event_id)  # Refresh
        
        ttk.Button(add_frame, text="Add Guest", command=add_guest).pack(side=tk.LEFT, padx=10)
        ttk.Button(add_frame, text="Send Invitations", 
                  command=lambda: self.send_invitations(event)).pack(side=tk.LEFT, padx=10)
        
        # Guests list
        if event['guests']:
            list_frame = ttk.Frame(guest_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            columns = ('Name', 'Email', 'Invited At')
            tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=200)
            
            for guest in event['guests']:
                tree.insert('', tk.END, values=(
                    guest['name'],
                    guest['email'],
                    guest['invited_at'][:10]  # Just the date part
                ))
            
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Remove guest button
            def remove_guest():
                selection = tree.selection()
                if not selection:
                    messagebox.showwarning("Warning", "Please select a guest to remove")
                    return
                
                guest_email = tree.item(selection[0])['values'][1]
                event['guests'] = [g for g in event['guests'] if g['email'] != guest_email]
                
                # Update events data
                events = self.load_data(self.events_file)
                for e in events:
                    if e['id'] == event_id:
                        e['guests'] = event['guests']
                        break
                
                if self.save_data(self.events_file, events):
                    messagebox.showinfo("Success", "Guest removed successfully")
                    self.manage_event_guests(event_id)
            
            ttk.Button(guest_frame, text="Remove Selected Guest", 
                      command=remove_guest).pack(pady=10)
        else:
            ttk.Label(guest_frame, text="No guests added yet").pack(pady=20)
    
    def send_invitations(self, event):
        """Send email invitations to all guests"""
        if not event['guests']:
            messagebox.showwarning("Warning", "No guests to send invitations to")
            return
        
        # In a real application, you would implement actual email sending
        # This is a simulation
        
        invitation_links = []
        for guest in event['guests']:
            # Generate unique invitation link (simulated)
            invitation_link = f"http://yourapp.com/events/{event['id']}/join?token={self.generate_password(16)}"
            invitation_links.append((guest['name'], guest['email'], invitation_link))
        
        # Show invitation summary
        summary = f"Invitations ready to send for: {event['name']}\n\n"
        summary += f"Event Password: {event['password']}\n\n"
        summary += "Guests:\n"
        for name, email, link in invitation_links:
            summary += f"- {name} ({email})\n"
            summary += f"  Link: {link}\n\n"
        
        messagebox.showinfo("Invitation Summary", 
                          f"{summary}\n\nIn a real application, these would be sent via email.")
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
        self.show_login_screen()

def main():
    try:
        root = tk.Tk()
        app = EventPlannerApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"The application encountered an error:\n{str(e)}")

if __name__ == "__main__":
    main()