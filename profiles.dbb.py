import sqlite3
import re
import tkinter as tk
from tkinter import ttk, messagebox

class Database:
    """Handles all SQLite database operations for person profiles."""
    def __init__(self, db_name="profiles.db"):
        self.db_name = db_name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS person_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        full_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        city TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        occupation TEXT NOT NULL
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to create table: {e}")

    def insert_profile(self, full_name, email, phone, city, age, occupation):
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO person_profiles (full_name, email, phone, city, age, occupation)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (full_name, email, phone, city, age, occupation))
                conn.commit()
                return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to insert record: {e}")
            return False

    def fetch_all(self):
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM person_profiles")
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch records: {e}")
            return []

    def update_profile(self, profile_id, full_name, email, phone, city, age, occupation):
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE person_profiles 
                    SET full_name = ?, email = ?, phone = ?, city = ?, age = ?, occupation = ?
                    WHERE id = ?
                """, (full_name, email, phone, city, age, occupation, profile_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update record: {e}")
            return False

    def delete_profile(self, profile_id):
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM person_profiles WHERE id = ?", (profile_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete record: {e}")
            return False

    def search_profiles(self, query):
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                search_term = f"%{query}%"
                cursor.execute("""
                    SELECT * FROM person_profiles 
                    WHERE full_name LIKE ? OR city LIKE ? OR occupation LIKE ?
                """, (search_term, search_term, search_term))
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Search failed: {e}")
            return []


class ProfileApp:
    """Handles the Tkinter Graphical User Interface and event bindings."""
    def __init__(self, root):
        self.root = root
        self.root.title("Person Profile Management System - ITPE 2113 Practical")
        self.root.geometry("1100x600")
        self.root.minsize(900, 500)

        self.db = Database()
        self.selected_profile_id = None

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = ttk.LabelFrame(self.main_pane, text=" Profile Entry Form ", padding=15)
        self.main_pane.add(self.left_frame, weight=1)

        self.right_frame = ttk.LabelFrame(self.main_pane, text=" Profile Records ", padding=15)
        self.main_pane.add(self.right_frame, weight=2)

        self.create_form_widgets()
        self.create_table_widgets()

        self.load_data()

    def create_form_widgets(self):
        fields = [
            ("Full Name:", "name_entry"),
            ("Email Address:", "email_entry"),
            ("Phone Number:", "phone_entry"),
            ("City:", "city_entry"),
            ("Age:", "age_entry"),
            ("Occupation:", "occupation_entry")
        ]

        self.entries = {}

        for idx, (label_text, attr_name) in enumerate(fields):
            label = ttk.Label(self.left_frame, text=label_text, font=("Arial", 10, "bold"))
            label.grid(row=idx*2, column=0, sticky="w", pady=(5, 2))
            
            entry = ttk.Entry(self.left_frame, font=("Arial", 10), width=30)
            entry.grid(row=idx*2+1, column=0, sticky="ew", pady=(0, 10))
            self.entries[attr_name] = entry

        btn_frame = ttk.Frame(self.left_frame)
        btn_frame.grid(row=len(fields)*2, column=0, sticky="ew", pady=15)
        btn_frame.columnconfigure((0, 1), weight=1)

        self.btn_add = ttk.Button(btn_frame, text="Add Profile", command=self.add_profile)
        self.btn_add.grid(row=0, column=0, padx=2, pady=5, sticky="ew")

        self.btn_update = ttk.Button(btn_frame, text="Update Selected", command=self.update_profile)
        self.btn_update.grid(row=0, column=1, padx=2, pady=5, sticky="ew")

        self.btn_delete = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_profile)
        self.btn_delete.grid(row=1, column=0, padx=2, pady=5, sticky="ew")

        self.btn_clear = ttk.Button(btn_frame, text="Clear Form", command=self.clear_form)
        self.btn_clear.grid(row=1, column=1, padx=2, pady=5, sticky="ew")

    def create_table_widgets(self):
        search_frame = ttk.Frame(self.right_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_records)

        self.btn_clear_filter = ttk.Button(search_frame, text="Clear Filter", command=self.clear_filter)
        self.btn_clear_filter.pack(side=tk.LEFT)

        table_container = ttk.Frame(self.right_frame)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Full Name", "Email", "Phone", "City", "Age", "Occupation")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")

        column_widths = { "ID": 40, "Full Name": 130, "Email": 150, "Phone": 100, "City": 90, "Age": 50, "Occupation": 110 }
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100), anchor=tk.W)

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def validate_inputs(self):
        name = self.entries["name_entry"].get().strip()
        email = self.entries["email_entry"].get().strip()
        phone = self.entries["phone_entry"].get().strip()
        city = self.entries["city_entry"].get().strip()
        age_str = self.entries["age_entry"].get().strip()
        occupation = self.entries["occupation_entry"].get().strip()

        if not all([name, email, phone, city, age_str, occupation]):
            messagebox.showerror("Validation Error", "All fields must be filled out.")
            return None

        try:
            age = int(age_str)
            if not (1 <= age <= 120):
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Age must be a valid positive integer between 1 and 120.")
            return None

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, email):
            messagebox.showerror("Validation Error", "Please enter a valid email address (e.g., user@example.com).")
            return None

        return name, email, phone, city, age, occupation

    def add_profile(self):
        data = self.validate_inputs()
        if data:
            success = self.db.insert_profile(*data)
            if success:
                messagebox.showinfo("Success", "Profile added successfully!")
                self.clear_form()
                self.load_data()

    def update_profile(self):
        if self.selected_profile_id is None:
            messagebox.showwarning("Selection Warning", "Please select a profile record from the table to update.")
            return

        data = self.validate_inputs()
        if data:
            success = self.db.update_profile(self.selected_profile_id, *data)
            if success:
                messagebox.showinfo("Success", "Profile updated successfully!")
                self.clear_form()
                self.load_data()

    def delete_profile(self):
        if self.selected_profile_id is None:
            messagebox.showwarning("Selection Warning", "Please select a profile record from the table to delete.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this profile record?")
        if confirm:
            success = self.db.delete_profile(self.selected_profile_id)
            if success:
                messagebox.showinfo("Success", "Profile deleted successfully!")
                self.clear_form()
                self.load_data()

    def load_data(self, records=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = records if records is not None else self.db.fetch_all()
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def on_row_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        values = self.tree.item(item, "values")
        
        if values:
            self.selected_profile_id = values[0]
            
            fields_keys = ["name_entry", "email_entry", "phone_entry", "city_entry", "age_entry", "occupation_entry"]
            for idx, key in enumerate(fields_keys, start=1):
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, values[idx])

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.selected_profile_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def filter_records(self, event):
        query = self.search_entry.get().strip()
        if not query:
            self.load_data()
            return
        
        filtered_rows = self.db.search_profiles(query)
        self.load_data(filtered_rows)

    def clear_filter(self):
        self.search_entry.delete(0, tk.END)
        self.load_data()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfileApp(root)
    root.mainloop()
