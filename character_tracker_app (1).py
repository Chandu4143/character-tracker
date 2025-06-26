import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os

# --- Constants ---
SAVE_FILE = "character_data_v6.json"
MAX_LEVEL = 200
BASE_EXP = 100
GROWTH_FACTOR = 1.5
CORE_ATTRIBUTES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
EQUIPMENT_SLOTS = ["Weapon", "Shield", "Helmet", "Chestplate", "Leggings", "Boots", "Ring 1", "Ring 2", "Amulet"]
ITEM_TYPES = ["Weapon", "Shield", "Helmet", "Chestplate", "Leggings", "Boots", "Ring", "Amulet", "Consumable", "Material", "Quest Item", "Other"]

# --- THEME AND STYLE ---
class Themes:
    FONT_FAMILY = "Segoe UI"
    FONT_NORMAL = (FONT_FAMILY, 10)
    FONT_BOLD = (FONT_FAMILY, 10, "bold")
    FONT_HEADER = (FONT_FAMILY, 14, "bold")
    FONT_ITALIC = (FONT_FAMILY, 9, "italic")

    dark = {
        "BACKGROUND": "#2E2E2E",
        "FOREGROUND": "#F5F5F5",
        "WIDGET_BG": "#3C3C3C",
        "WIDGET_FG": "#FFFFFF",
        "ACCENT_COLOR": "#007ACC",
        "TREEVIEW_ODD": "#3C3C3C",
        "TREEVIEW_EVEN": "#333333"
    }
    light = {
        "BACKGROUND": "#F0F0F0",
        "FOREGROUND": "#000000",
        "WIDGET_BG": "#FFFFFF",
        "WIDGET_FG": "#000000",
        "ACCENT_COLOR": "#0078D7",
        "TREEVIEW_ODD": "#F0F0F0",
        "TREEVIEW_EVEN": "#E0E0E0"
    }

# --- Utility Functions ---
def generate_exp_table():
    return [0] + [int(BASE_EXP * (lvl ** GROWTH_FACTOR)) for lvl in range(1, MAX_LEVEL + 1)]

EXP_TABLE = generate_exp_table()

# --- Data and Logic Layer ---
class Item:
    def __init__(self, name, description="", quantity=1, item_type="Other", effects=None):
        self.name = name
        self.description = description
        self.quantity = quantity
        self.item_type = item_type
        self.effects = effects if effects is not None else {}

class Character:
    def __init__(self, name="", level=1, exp=0, skills=None, notes="", inventory=None, equipment=None, attributes=None):
        self.name = name
        self.level = level
        self.exp = exp
        self.skills = skills if skills is not None else []
        self.notes = notes
        self.inventory = inventory if inventory is not None else []
        self.equipment = equipment if equipment is not None else {slot: None for slot in EQUIPMENT_SLOTS}
        self.attributes = attributes if attributes is not None else {
            "Strength": 10, "Dexterity": 10, "Constitution": 10,
            "Intelligence": 10, "Wisdom": 10, "Charisma": 10
        }

    def get_health(self):
        return 100 + (self.attributes["Constitution"] - 10) * 5

    def get_mana(self):
        return 100 + (self.attributes["Intelligence"] - 10) * 5

    def get_total_attribute(self, attr_name):
        base_value = self.attributes.get(attr_name, 0)
        bonus = 0
        for item in self.equipment.values():
            if item and hasattr(item, 'effects') and item.effects:
                bonus += item.effects.get(attr_name, 0)
        return base_value + bonus

    def get_attribute_modifier(self, attr_name):
        """Calculates the attribute modifier based on the total score (e.g., D&D style)."""
        total_score = self.get_total_attribute(attr_name)
        return (total_score - 10) // 2

    def get_exp_for_next_level(self, level):
        if 1 <= level < MAX_LEVEL:
            return EXP_TABLE[level]
        return float('inf')

    def add_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.level < MAX_LEVEL and self.exp >= self.get_exp_for_next_level(self.level):
            self.exp -= self.get_exp_for_next_level(self.level)
            self.level += 1
            leveled_up = True
        return leveled_up

    def remove_exp(self, amount):
        self.exp -= amount
        leveled_down = False
        while self.level > 1 and self.exp < 0:
            self.level -= 1
            self.exp += self.get_exp_for_next_level(self.level)
            leveled_down = True
        if self.exp < 0:
            self.exp = 0
        return leveled_down

    def add_skill_exp(self, skill_index, amount):
        if 0 <= skill_index < len(self.skills):
            skill = self.skills[skill_index]
            skill['exp'] += amount
            leveled_up = False
            while skill['level'] < MAX_LEVEL and skill['exp'] >= self.get_exp_for_next_level(skill['level']):
                skill['exp'] -= self.get_exp_for_next_level(skill['level'])
                skill['level'] += 1
                leveled_up = True
        return leveled_up, skill.get('level')

    def remove_skill_exp(self, skill_index, amount):
        if 0 <= skill_index < len(self.skills):
            skill = self.skills[skill_index]
            skill['exp'] -= amount
            leveled_down = False
            while skill['level'] > 1 and skill['exp'] < 0:
                skill['level'] -= 1
                skill['exp'] += self.get_exp_for_next_level(skill['level'])
                leveled_down = True
            if skill['exp'] < 0:
                skill['exp'] = 0
            return leveled_down, skill.get('level')
        return False, None

    def add_skill(self, name):
        if any(s['name'] == name for s in self.skills):
            return False
        self.skills.append({'name': name, 'level': 1, 'exp': 0})
        return True

    def update_skill(self, index, **kwargs):
        if 0 <= index < len(self.skills):
            self.skills[index].update(kwargs)
            return True
        return False

    def remove_skill(self, index):
        if 0 <= index < len(self.skills):
            del self.skills[index]
            return True
        return False

class PersistenceManager:
    def __init__(self, filepath):
        self.filepath = filepath

    def save(self, characters, theme_name, active_char_name):
        characters_data = {}
        for name, char in characters.items():
            char_dict = char.__dict__.copy()
            char_dict['inventory'] = [item.__dict__ for item in char.inventory]
            char_dict['equipment'] = {slot: item.__dict__ if item else None for slot, item in char.equipment.items()}
            characters_data[name] = char_dict

        data = {
            "theme": theme_name,
            "active_character": active_char_name,
            "characters": characters_data
        }
        try:
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except IOError as e:
            messagebox.showerror("Save Error", f"Failed to save data to {self.filepath}\n{e}")
            return False

    def load(self):
        if not os.path.exists(self.filepath):
            return {}, "dark", None
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                theme_name = data.get("theme", "dark")
                active_char_name = data.get("active_character")
                characters_data = data.get("characters", {})
                characters = {}
                for name, char_data in characters_data.items():
                    inventory = [Item(**item_data) for item_data in char_data.get('inventory', [])]
                    equipment_data = char_data.get('equipment', {})
                    equipment = {slot: Item(**item_data) if item_data else None for slot, item_data in equipment_data.items()}
                    for slot in EQUIPMENT_SLOTS:
                        if slot not in equipment:
                            equipment[slot] = None

                    char_data['inventory'] = inventory
                    char_data['equipment'] = equipment
                    characters[name] = Character(**char_data)

                return characters, theme_name, active_char_name
        except (IOError, json.JSONDecodeError) as e:
            messagebox.showerror("Load Error", f"Failed to load data from {self.filepath}\n{e}")
            return {}, "dark", None

# --- UI Layer ---
class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text, theme):
        self.widget = widget
        self.text = text
        self.theme = theme
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def set_theme(self, theme):
        self.theme = theme

    def enter(self, event=None):
        if self.tooltip:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        bg = self.theme.get("WIDGET_BG", "#3C3C3C")
        fg = self.theme.get("WIDGET_FG", "#FFFFFF")

        label = ttk.Label(self.tooltip, text=self.text, justify='left',
                          background=bg, foreground=fg, relief='solid', borderwidth=1,
                          font=Themes.FONT_ITALIC, padding=5)
        label.pack()

    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class CharacterTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Character Tracker v6.1 - Polished UI")
        self.root.geometry("950x750")

        self.pm = PersistenceManager(SAVE_FILE)
        self.characters, self.theme_name, active_char_name = self.pm.load()
        
        if not self.characters:
            default_char = Character(name="Default Character")
            self.characters = {default_char.name: default_char}
        
        self.active_character_name = active_char_name if active_char_name in self.characters else list(self.characters.keys())[0]

        self.theme = Themes.dark if self.theme_name == "dark" else Themes.light
        self.tooltips = []

        # --- Search/Filter Variables ---
        self.skill_search_var = tk.StringVar()
        self.inventory_search_var = tk.StringVar()
        self.skill_search_var.trace_add("write", self._on_skill_search)
        self.inventory_search_var.trace_add("write", self._on_inventory_search)
        self.skill_exp_progress_var = tk.DoubleVar()
        self.skill_exp_label_var = tk.StringVar(value="Select a skill to see progress")
        self.skill_exp_progress_label_var = tk.StringVar()

        # --- Sort State ---
        self.skill_sort_column = "Skill Name"
        self.skill_sort_reverse = False
        self.inventory_sort_column = "Item Name"
        self.inventory_sort_reverse = False


        self._apply_styles()
        self._setup_ui()
        self._update_all_views()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    @property
    def current_character(self):
        return self.characters.get(self.active_character_name)

    def _validate_integer_input(self, P):
        """Validation command to allow only integers in an Entry widget."""
        # P is the value of the entry if the edit is allowed
        return str.isdigit(P) or P == ""

    def _apply_styles(self):
        self.root.configure(bg=self.theme["BACKGROUND"])
        style = ttk.Style(self.root)
        style.theme_use('clam')

        style.configure('.', background=self.theme["BACKGROUND"], foreground=self.theme["FOREGROUND"], font=Themes.FONT_NORMAL)
        style.configure('TFrame', background=self.theme["BACKGROUND"])
        style.configure('TLabel', background=self.theme["BACKGROUND"], foreground=self.theme["FOREGROUND"], font=Themes.FONT_NORMAL)
        style.configure('TButton', background=self.theme["ACCENT_COLOR"], foreground=Themes.light["WIDGET_FG"], font=Themes.FONT_BOLD, borderwidth=0)
        style.map('TButton', background=[('active', self.theme["ACCENT_COLOR"])])
        style.configure('TEntry', fieldbackground=self.theme["WIDGET_BG"], foreground=self.theme["WIDGET_FG"], insertcolor=self.theme["WIDGET_FG"])
        style.configure('TCombobox', fieldbackground=self.theme["WIDGET_BG"], foreground=self.theme["WIDGET_FG"], selectbackground=self.theme["WIDGET_BG"], selectforeground=self.theme["WIDGET_FG"])
        style.configure('TLabelframe', background=self.theme["BACKGROUND"], foreground=self.theme["FOREGROUND"], font=Themes.FONT_BOLD)
        style.configure('TLabelframe.Label', background=self.theme["BACKGROUND"], foreground=self.theme["FOREGROUND"], font=Themes.FONT_BOLD)

        style.configure("TNotebook", background=self.theme["BACKGROUND"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.theme["WIDGET_BG"], foreground=self.theme["FOREGROUND"], font=Themes.FONT_BOLD, padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", self.theme["ACCENT_COLOR"]), ("active", "#4a4a4a")])

        style.configure("Treeview", background=self.theme["WIDGET_BG"], fieldbackground=self.theme["WIDGET_BG"], foreground=self.theme["WIDGET_FG"], font=Themes.FONT_NORMAL)
        style.configure("Treeview.Heading", background=self.theme["ACCENT_COLOR"], foreground=Themes.light["WIDGET_FG"], font=Themes.FONT_BOLD, relief="flat")
        style.map("Treeview.Heading", background=[('active', self.theme["ACCENT_COLOR"])])
        style.configure("green.Horizontal.TProgressbar", background=self.theme["ACCENT_COLOR"])
        self.root.option_add("*TCombobox*Listbox*Background", self.theme["WIDGET_BG"])
        self.root.option_add("*TCombobox*Listbox*Foreground", self.theme["WIDGET_FG"])

    def _setup_ui(self):
        top_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        top_frame.pack(fill="x")

        self._create_character_manager(top_frame)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self._create_status_tab()
        self._create_attributes_tab()
        self._create_skills_tab()
        self._create_inventory_tab()
        self._create_notes_tab()

    def _create_character_manager(self, parent):
        frame = ttk.LabelFrame(parent, text="Character Management", padding=10)
        frame.pack(fill="x")

        ttk.Label(frame, text="Active Character:").pack(side="left", padx=(0, 5))
        self.character_selector_var = tk.StringVar(value=self.active_character_name)
        self.character_selector = ttk.Combobox(frame, textvariable=self.character_selector_var, state="readonly", width=25, font=Themes.FONT_NORMAL)
        self.character_selector.pack(side="left", padx=5)
        self.character_selector.bind("<<ComboboxSelected>>", self._on_character_select)

        add_btn = ttk.Button(frame, text="Add New", command=self._add_character)
        add_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(add_btn, "Add a new character profile.", self.theme))

        rename_btn = ttk.Button(frame, text="Rename", command=self._rename_character)
        rename_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(rename_btn, "Rename the current character.", self.theme))

        delete_btn = ttk.Button(frame, text="Delete", command=self._delete_character)
        delete_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(delete_btn, "Delete the current character.", self.theme))

        export_btn = ttk.Button(frame, text="Export", command=self._export_character)
        export_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(export_btn, "Export the current character sheet to a text file.", self.theme))

        self.theme_button = ttk.Button(frame, text="Toggle Theme", command=self._toggle_theme)
        self.theme_button.pack(side="right")
        self.tooltips.append(ToolTip(self.theme_button, "Switch between light and dark themes.", self.theme))

    def _create_status_tab(self):
        """Creates the 'Status' tab with character info and EXP controls."""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="Status")

        self._init_status_vars()
        self._create_status_info_frame(tab)
        self._create_status_exp_controls(tab)

    def _init_status_vars(self):
        """Initializes Tkinter variables for the Status tab."""
        self.name_var = tk.StringVar()
        self.level_var = tk.IntVar()
        self.exp_var = tk.IntVar()
        self.exp_to_next_var = tk.StringVar()
        self.main_exp_gain = tk.IntVar()
        self.health_var = tk.StringVar()
        self.mana_var = tk.StringVar()
        self.exp_progress_var = tk.DoubleVar()
        self.exp_progress_label_var = tk.StringVar()
    
    def _create_status_info_frame(self, parent_tab):
        """Creates the frame displaying character's core status information."""
        status_frame = ttk.Frame(parent_tab)
        status_frame.pack(fill='x', pady=10)

        # Define labels and their corresponding Tkinter variables
        info_fields = [
            ("Name:", self.name_var),
            ("Level:", self.level_var),
            ("Current EXP:", self.exp_var),
            ("EXP to Next:", self.exp_to_next_var),
            ("Health:", self.health_var),
            ("Mana:", self.mana_var)
        ]

        for i, (label_text, var) in enumerate(info_fields):
            ttk.Label(status_frame, text=label_text, font=Themes.FONT_BOLD).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            entry = ttk.Entry(status_frame, textvariable=var, state='readonly', font=Themes.FONT_NORMAL)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            if label_text == "Name:":
                entry.config(width=30) # Specific width for the name entry
        
        # --- EXP Progress Bar ---
        progress_frame = ttk.Frame(status_frame)
        progress_frame.grid(row=i + 1, column=0, columnspan=2, sticky='ew', pady=(20, 0))
        
        progress_bar = ttk.Progressbar(progress_frame, variable=self.exp_progress_var, style="green.Horizontal.TProgressbar", length=300)
        progress_bar.pack(fill='x')

        # Overlay label on the progress bar
        progress_label = ttk.Label(progress_frame, textvariable=self.exp_progress_label_var, background=self.theme["ACCENT_COLOR"], foreground=Themes.light["WIDGET_FG"], font=Themes.FONT_BOLD)
        progress_label.place(relx=0.5, rely=0.5, anchor="center")

    def _create_status_exp_controls(self, parent_tab):
        """Creates the frame for adding/removing character experience."""
        exp_frame = ttk.LabelFrame(parent_tab, text="Add Character Experience", padding="15")
        exp_frame.pack(fill="x", pady=20)

        vcmd = (self.root.register(self._validate_integer_input), '%P')

        ttk.Label(exp_frame, text="Amount:").pack(side="left", padx=5)
        ttk.Entry(exp_frame, textvariable=self.main_exp_gain, width=15, validate='key', validatecommand=vcmd).pack(side="left", padx=5, expand=True, fill="x")
        
        apply_exp_btn = ttk.Button(exp_frame, text="Apply EXP", command=self._apply_main_exp)
        apply_exp_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(apply_exp_btn, "Add EXP to the character's main level.", self.theme))

        remove_exp_btn = ttk.Button(exp_frame, text="Remove EXP", command=self._remove_main_exp)
        remove_exp_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(remove_exp_btn, "Remove EXP from the character's main level.", self.theme))

    def _create_attributes_tab(self):
        """Creates the 'Attributes' tab with core attribute display and editing."""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="Attributes")

        self._init_attribute_vars()
        self._create_attribute_display_frame(tab)
    
    def _init_attribute_vars(self):
        """Initializes Tkinter variables for attributes."""
        self.attribute_vars = {attr: tk.IntVar() for attr in self.current_character.attributes.keys()}
        self.total_attribute_vars = {attr: tk.StringVar() for attr in self.current_character.attributes.keys()}
        self.attribute_modifier_vars = {attr: tk.StringVar() for attr in self.current_character.attributes.keys()}
    
    def _create_attribute_display_frame(self, parent_tab):
        """Creates the frame displaying core attributes."""
        attr_frame = ttk.LabelFrame(parent_tab, text="Core Attributes", padding=15)
        attr_frame.pack(fill='x')

        ttk.Label(attr_frame, text="Attribute", font=Themes.FONT_BOLD).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(attr_frame, text="Base", font=Themes.FONT_BOLD).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        ttk.Label(attr_frame, text="Total", font=Themes.FONT_BOLD).grid(row=0, column=2, sticky='w', padx=5, pady=2)
        ttk.Label(attr_frame, text="Modifier", font=Themes.FONT_BOLD).grid(row=0, column=3, sticky='w', padx=5, pady=2)

        vcmd = (self.root.register(self._validate_integer_input), '%P')

        row = 1 # Start from row 1 for attribute entries
        for attr, var in self.attribute_vars.items():
            ttk.Label(attr_frame, text=f"{attr}:", font=Themes.FONT_NORMAL).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            entry = ttk.Entry(attr_frame, textvariable=var, width=10, font=Themes.FONT_NORMAL, validate='key', validatecommand=vcmd)
            entry.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
            entry.bind("<FocusOut>", self._on_attribute_change)
            ttk.Label(attr_frame, textvariable=self.total_attribute_vars[attr], font=Themes.FONT_NORMAL).grid(row=row, column=2, sticky='w', padx=5, pady=5)
            ttk.Label(attr_frame, textvariable=self.attribute_modifier_vars[attr], font=Themes.FONT_BOLD).grid(row=row, column=3, sticky='w', padx=5, pady=5)
            row += 1
    
    def _on_attribute_change(self, event=None):
        if not self.current_character:
            return
        for attr, var in self.attribute_vars.items():
            try:
                self.current_character.attributes[attr] = var.get()
            except tk.TclError:
                # Handle cases where the entry might not have a valid integer
                pass
        self._update_status_view() # Refresh derived stats

    def _create_skills_tab(self):
        """Creates the 'Skills' tab with a Treeview for skills and EXP controls."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Skills")

        self._create_skill_search_bar(tab)
        self._create_skill_tree_view(tab)
        self._create_skill_controls(tab)

    def _create_skill_tree_view(self, parent_tab):
        """Creates the Treeview widget for displaying skills."""
        tree_frame = ttk.Frame(parent_tab)
        tree_frame.pack(fill="both", expand=True)
        columns = ("#1", "#2", "#3", "#4")
        self.skill_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        headings = {"#1": "Skill Name", "#2": "Level", "#3": "Current EXP", "#4": "EXP to Next"}
        for col, text in headings.items():
            self.skill_tree.heading(col, text=text, command=lambda c=text: self._sort_skills_column(c))

        self.skill_tree.column("#1", width=250, anchor="w")
        self.skill_tree.column("#2", width=100, anchor="center")
        self.skill_tree.column("#3", width=120, anchor="center")
        self.skill_tree.column("#4", width=120, anchor="center")
        self.skill_tree.pack(side="left", fill="both", expand=True, pady=5)
        self.skill_tree.bind("<<TreeviewSelect>>", self._on_skill_select)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.skill_tree.yview)
        self.skill_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def _create_skill_search_bar(self, parent_tab):
        """Creates a search bar for filtering skills."""
        search_frame = ttk.Frame(parent_tab)
        search_frame.pack(fill="x", pady=(0, 5), padx=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.skill_search_var)
        search_entry.pack(side="left", fill="x", expand=True)
    
    def _create_skill_controls(self, parent_tab):
        """Creates buttons and EXP input for skill management."""
        btn_frame = ttk.Frame(parent_tab)
        btn_frame.pack(pady=10, fill="x")
        
        add_skill_btn = ttk.Button(btn_frame, text="Add Skill", command=self._add_skill)
        add_skill_btn.pack(side="left", padx=10)
        self.tooltips.append(ToolTip(add_skill_btn, "Add a new skill to the list.", self.theme))
        
        exp_frame = ttk.LabelFrame(parent_tab, text="Add Experience to Selected Skill", padding="15")
        exp_frame.pack(fill="x", pady=10)
        self.skill_exp_gain = tk.IntVar()

        # --- Skill Progress Bar ---
        skill_progress_frame = ttk.Frame(exp_frame)
        skill_progress_frame.pack(fill='x', pady=(0, 10), expand=True)

        # Label for skill name (above the bar)
        ttk.Label(skill_progress_frame, textvariable=self.skill_exp_label_var, font=Themes.FONT_ITALIC).pack()

        # Container for the progress bar and its overlay text
        bar_container = ttk.Frame(skill_progress_frame)
        bar_container.pack(fill='x', pady=(5,0), expand=True)
        ttk.Progressbar(bar_container, variable=self.skill_exp_progress_var, style="green.Horizontal.TProgressbar").pack(fill='x', expand=True)

        skill_progress_label = ttk.Label(bar_container, textvariable=self.skill_exp_progress_label_var, background=self.theme["ACCENT_COLOR"], foreground=Themes.light["WIDGET_FG"], font=Themes.FONT_NORMAL)
        skill_progress_label.place(relx=0.5, rely=0.5, anchor="center")
        vcmd = (self.root.register(self._validate_integer_input), '%P')
        ttk.Label(exp_frame, text="Amount:").pack(side="left", padx=5)
        ttk.Entry(exp_frame, textvariable=self.skill_exp_gain, width=15, validate='key', validatecommand=vcmd).pack(side="left", padx=5, expand=True, fill="x")
        
        apply_exp_btn = ttk.Button(exp_frame, text="Apply to Selected", command=self._apply_exp_to_skill)
        apply_exp_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(apply_exp_btn, "Add the specified EXP to the selected skill.", self.theme))

        remove_exp_btn = ttk.Button(exp_frame, text="Remove from Selected", command=self._remove_exp_from_skill)
        remove_exp_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(remove_exp_btn, "Remove the specified EXP from the selected skill.", self.theme))

        self.skill_context_menu = self._create_context_menu(self.skill_tree, [
            ("Edit Skill", self._edit_skill),
            ("Delete Skill", self._delete_skill)
        ])

    def _create_inventory_tab(self):
        """Creates the 'Inventory' tab with equipment, inventory, and item details."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Inventory")

        self._create_inventory_panes(tab)
        self._create_inventory_buttons(tab)

    def _create_inventory_panes(self, parent_tab):
        """Creates the paned window containing equipment and inventory treeviews."""
        main_pane = ttk.PanedWindow(parent_tab, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True)
        # --- Equipment Pane ---
        equip_frame = ttk.LabelFrame(main_pane, text="Equipment", padding=10)
        main_pane.add(equip_frame, weight=1)

        equip_cols = ("#1", "#2")
        self.equip_tree = ttk.Treeview(equip_frame, columns=equip_cols, show="headings", height=len(EQUIPMENT_SLOTS))
        self.equip_tree.heading("#1", text="Slot")
        self.equip_tree.heading("#2", text="Item Name")
        self.equip_tree.column("#1", width=100, anchor="w")
        self.equip_tree.column("#2", width=150, anchor="w")
        self.equip_tree.pack(fill="both", expand=True)
        self.equip_tree.bind("<<TreeviewSelect>>", self._on_item_select)
        # --- Inventory Pane ---
        inv_frame = ttk.LabelFrame(main_pane, text="Inventory", padding=10)
        main_pane.add(inv_frame, weight=2)

        # --- Inventory Search Bar ---
        inv_search_frame = ttk.Frame(inv_frame)
        inv_search_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(inv_search_frame, text="Search:").pack(side="left", padx=(0, 5))
        search_entry = ttk.Entry(inv_search_frame, textvariable=self.inventory_search_var)
        search_entry.pack(side="left", fill="x", expand=True)

        inv_cols = ("#1", "#2", "#3")
        self.inv_tree = ttk.Treeview(inv_frame, columns=inv_cols, show="headings", height=15)

        headings = {"#1": "Item Name", "#2": "Type", "#3": "Qty"}
        for col, text in headings.items():
            self.inv_tree.heading(col, text=text, command=lambda c=text: self._sort_inventory_column(c))

        self.inv_tree.column("#1", width=200, anchor="w")
        self.inv_tree.column("#2", width=100, anchor="w")
        self.inv_tree.column("#3", width=50, anchor="center")
        self.inv_tree.pack(fill="both", expand=True)
        self.inv_tree.bind("<<TreeviewSelect>>", self._on_item_select)
        # --- Description Label ---
        self.item_desc_label = ttk.Label(inv_frame, text="Click an item to see its description.", wraplength=400, justify="left", font=Themes.FONT_ITALIC)
        self.item_desc_label.pack(pady=(10,0), fill="x")
    
    def _create_inventory_buttons(self, parent_tab):
        """Creates buttons for adding, editing, and deleting items."""
        # --- Button Frame ---
        btn_frame = ttk.Frame(parent_tab)
        btn_frame.pack(fill="x", pady=10)

        add_item_btn = ttk.Button(btn_frame, text="Add Item", command=self._add_item)
        add_item_btn.pack(side="left", padx=5)
        self.tooltips.append(ToolTip(add_item_btn, "Add a new item to your inventory.", self.theme))

        # --- Context Menus ---
        self.inv_context_menu = self._create_context_menu(self.inv_tree, [
            ("Equip", self._equip_item),
            None, # Separator
            ("Edit", self._edit_item),
            ("Delete", self._delete_item)
        ])
        
        self.equip_context_menu = self._create_context_menu(self.equip_tree, [
            ("Unequip", self._unequip_item)
        ])

    def _create_notes_tab(self):
        """Creates the 'Notes' tab with a text area for character notes."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Notes")
        
        self._create_notes_text_area(tab)

    def _create_notes_text_area(self, parent_tab):
        """Creates the text widget for character notes."""
        text_frame = ttk.Frame(parent_tab)
        text_frame.pack(fill="both", expand=True)
        
        self.notes_text = tk.Text(text_frame, wrap='word', relief="flat", insertbackground=self.theme["WIDGET_FG"])
        # Bindings for smooth scroll and content modification
        self.notes_text.bind("<MouseWheel>", self._smooth_scroll_handler)
        self.notes_text.bind("<Button-4>", self._smooth_scroll_handler) # For Linux scroll up
        self.notes_text.bind("<Button-5>", self._smooth_scroll_handler) # For Linux scroll down
        self.notes_text.bind("<<Modified>>", self._on_notes_modified) # For saving changes

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.notes_text.yview)
        self.notes_text.config(yscrollcommand=scrollbar.set)
        self.notes_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    def _update_all_views(self):
        self._update_character_selector()
        if self.current_character:
            self._update_status_view()
            self._update_attributes_view()
            self._update_skills_view()
            self._update_inventory_views()
            self._update_notes_view()
            self._update_theme_specific_widgets()

    def _update_character_selector(self):
        self.character_selector['values'] = list(self.characters.keys())
        self.character_selector_var.set(self.active_character_name)

    def _update_status_view(self, *args):
        self.name_var.set(self.current_character.name)
        self.level_var.set(self.current_character.level)
        self.exp_var.set(self.current_character.exp)
        next_exp = self.current_character.get_exp_for_next_level(self.current_character.level)
        self.health_var.set(self.current_character.get_health())
        self.mana_var.set(self.current_character.get_mana())

        if next_exp != float('inf'):
            self.exp_to_next_var.set(f"{self.current_character.exp} / {next_exp}")
            progress = (self.current_character.exp / next_exp) * 100 if next_exp > 0 else 100
            self.exp_progress_var.set(progress)
            self.exp_progress_label_var.set(f"{self.current_character.exp} / {next_exp} ({progress:.1f}%)")
        else:
            self.exp_to_next_var.set("MAX LEVEL")
            self.exp_progress_var.set(100)
            self.exp_progress_label_var.set("MAX LEVEL")

        # Reset skill progress on character change
        self._reset_skill_progress_bar()

    def _update_attributes_view(self):
        for attr, var in self.attribute_vars.items():
            base_val = self.current_character.attributes.get(attr, 0)
            total_val = self.current_character.get_total_attribute(attr)
            modifier = self.current_character.get_attribute_modifier(attr)
            var.set(base_val)
            if total_val > base_val:
                self.total_attribute_vars[attr].set(f"{total_val} ({base_val} + {total_val - base_val})")
            else:
                self.total_attribute_vars[attr].set(total_val)
            self.attribute_modifier_vars[attr].set(f"{modifier:+}") # Show + for positive

    def _update_skills_view(self):
        # Add sort indicators to headers
        headings = {"#1": "Skill Name", "#2": "Level", "#3": "Current EXP", "#4": "EXP to Next"}
        arrow = ' \u25BC' if self.skill_sort_reverse else ' \u25B2'
        for col_id, text in headings.items():
            # Update header text with sort indicator
            if text == self.skill_sort_column:
                self.skill_tree.heading(col_id, text=text + arrow)
            else:
                self.skill_tree.heading(col_id, text=text)

        self.skill_tree.tag_configure('oddrow', background=self.theme["TREEVIEW_ODD"], foreground=self.theme["WIDGET_FG"])
        self.skill_tree.tag_configure('evenrow', background=self.theme["TREEVIEW_EVEN"], foreground=self.theme["WIDGET_FG"])
        for i in self.skill_tree.get_children():
            self.skill_tree.delete(i)
        self._reset_skill_progress_bar()

        search_term = self.skill_search_var.get().lower()
        
        filtered_skills = [
            (i, skill) for i, skill in enumerate(self.current_character.skills)
            if search_term in skill['name'].lower()
        ]

        # --- Sorting Logic ---
        sort_key_map = {
            "Skill Name": lambda item: item[1]['name'].lower(),
            "Level": lambda item: item[1]['level'],
            "Current EXP": lambda item: item[1]['exp'],
            "EXP to Next": lambda item: self.current_character.get_exp_for_next_level(item[1]['level'])
        }
        sort_key = sort_key_map.get(self.skill_sort_column)
        if sort_key:
            # Sort the list of (original_index, skill_dict) tuples
            filtered_skills.sort(key=sort_key, reverse=self.skill_sort_reverse)

        for i, (original_index, skill) in enumerate(filtered_skills):
            next_exp = self.current_character.get_exp_for_next_level(skill['level'])
            next_exp_str = str(next_exp) if next_exp != float('inf') else "MAX"
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Use original_index as the IID to link back to the original list
            self.skill_tree.insert("", "end", iid=original_index, values=(skill['name'], skill['level'], skill['exp'], next_exp_str), tags=(tag,))

    def _update_inventory_views(self):
        # Equipment view is not filtered
        for i in self.equip_tree.get_children():
            self.equip_tree.delete(i)
        for slot, item in self.current_character.equipment.items():
            item_name = item.name if item else "-"
            self.equip_tree.insert("", "end", values=(slot, item_name))

        # Add sort indicators to headers
        headings = {"#1": "Item Name", "#2": "Type", "#3": "Qty"}
        arrow = ' \u25BC' if self.inventory_sort_reverse else ' \u25B2'
        for col_id, text in headings.items():
            # Update header text with sort indicator
            if text == self.inventory_sort_column:
                self.inv_tree.heading(col_id, text=text + arrow)
            else:
                self.inv_tree.heading(col_id, text=text)

        # Inventory view is filtered
        for i in self.inv_tree.get_children():
            self.inv_tree.delete(i)

        search_term = self.inventory_search_var.get().lower()
        
        filtered_inventory = [
            (i, item) for i, item in enumerate(self.current_character.inventory)
            if search_term in item.name.lower()
        ]

        # --- Sorting Logic ---
        sort_key_map = {
            "Item Name": lambda item: item[1].name.lower(),
            "Type": lambda item: item[1].item_type.lower(),
            "Qty": lambda item: item[1].quantity
        }
        sort_key = sort_key_map.get(self.inventory_sort_column)
        if sort_key:
            # Sort the list of (original_index, item_obj) tuples
            filtered_inventory.sort(key=sort_key, reverse=self.inventory_sort_reverse)

        for i, (original_index, item) in enumerate(filtered_inventory):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Use original_index as the IID to link back to the original list
            self.inv_tree.insert("", "end", iid=original_index, values=(item.name, item.item_type, item.quantity), tags=(tag,))
        
        self.item_desc_label.config(text="Click an item to see its description.")
        self._update_attributes_view() # Update attributes when equipment changes

    def _update_notes_view(self):
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", self.current_character.notes)
        self.notes_text.edit_modified(False)

    def _update_theme_specific_widgets(self):
        """Updates widgets that need manual theme configuration."""
        self.notes_text.config(bg=self.theme["WIDGET_BG"], fg=self.theme["WIDGET_FG"], insertbackground=self.theme["WIDGET_FG"])

    def _create_context_menu(self, treeview, commands):
        menu = tk.Menu(treeview, tearoff=0, bg=self.theme["WIDGET_BG"], fg=self.theme["FOREGROUND"])
        for item in commands:
            if item is None:
                menu.add_separator()
            else:
                label, command = item
                menu.add_command(label=label, command=command)

        def show_menu(event):
            iid = treeview.identify_row(event.y)
            if iid:
                treeview.selection_set(iid)
                treeview.focus(iid)
                menu.post(event.x_root, event.y_root)

        treeview.bind("<Button-3>", show_menu)
        return menu

    def _smooth_scroll_handler(self, event):
        """Handles mouse wheel events and initiates smooth scrolling for the Notes tab."""
        # Stop any ongoing scroll animation to prevent conflicts
        if hasattr(self, "_scroll_job"):
            self.root.after_cancel(self._scroll_job)

        # Determine scroll direction and magnitude (cross-platform)
        if event.num == 5 or event.delta < 0:
            delta = 120  # Standard delta for one wheel click down
        else:
            delta = -120 # Standard delta for one wheel click up

        self._perform_smooth_scroll(delta)
        return "break" # Prevent the default, jarring scroll behavior

    def _perform_smooth_scroll(self, delta, step=0):
        """Recursively scrolls the text widget to create a smooth, eased-out effect."""
        total_steps = 15
        if step < total_steps:
            # Ease-out: move less as we approach the end of the animation
            fraction_to_scroll = delta / total_steps
            self.notes_text.yview_scroll(int(fraction_to_scroll / 10), "units") # Divide for finer control
            
            self._scroll_job = self.root.after(12, self._perform_smooth_scroll, delta, step + 1)

    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = Themes.light if self.theme_name == "light" else Themes.dark
        self._apply_styles()
        self._update_all_views()
        for tooltip in self.tooltips:
            tooltip.set_theme(self.theme)
        
        for menu in [self.skill_context_menu, self.inv_context_menu, self.equip_context_menu]:
            menu.config(bg=self.theme["WIDGET_BG"], fg=self.theme["FOREGROUND"])

    def _on_item_select(self, event):
        if not self.current_character: return
        
        source_widget = event.widget
        item = None

        try:
            if source_widget == self.inv_tree:
                selected_item_iid = self.inv_tree.focus()
                if selected_item_iid:
                    item = self.current_character.inventory[int(selected_item_iid)]
            elif source_widget == self.equip_tree:
                selected_item_iid = self.equip_tree.focus()
                if selected_item_iid:
                    slot = self.equip_tree.item(selected_item_iid, 'values')[0]
                    item = self.current_character.equipment.get(slot)
        except (IndexError, ValueError):
            item = None # Item may have been deleted

        if item and item.description:
            self.item_desc_label.config(text=f"Description: {item.description}")
        elif item:
            self.item_desc_label.config(text="No description for this item.")
        else:
            self.item_desc_label.config(text="Click an item to see its description.")

    def _on_character_select(self, event):
        new_name = self.character_selector_var.get()
        if new_name and new_name != self.active_character_name:
            self._sync_ui_to_character()
            self.active_character_name = new_name
            self._update_all_views()

    def _on_skill_select(self, event=None):
        if not self.current_character: return
        selected_iid = self.skill_tree.focus()
        if not selected_iid:
            self._reset_skill_progress_bar()
            return

        try:
            index = int(selected_iid)
            skill = self.current_character.skills[index]
            current_exp = skill['exp']
            next_exp = self.current_character.get_exp_for_next_level(skill['level'])

            if next_exp != float('inf'):
                progress = (current_exp / next_exp) * 100 if next_exp > 0 else 100
                self.skill_exp_progress_var.set(progress)
                self.skill_exp_label_var.set(f"{skill['name']}:")
                self.skill_exp_progress_label_var.set(f"{current_exp} / {next_exp} ({progress:.1f}%)")
            else:
                self.skill_exp_progress_var.set(100)
                self.skill_exp_label_var.set(f"{skill['name']} is at MAX LEVEL")
                self.skill_exp_progress_label_var.set("MAX")

        except (IndexError, ValueError):
            self._reset_skill_progress_bar()

    def _reset_skill_progress_bar(self):
        self.skill_exp_progress_var.set(0)
        self.skill_exp_label_var.set("Select a skill to see progress")
        self.skill_exp_progress_label_var.set("")

    def _sort_skills_column(self, col):
        """Handles sorting of the skills treeview when a column header is clicked."""
        if self.skill_sort_column == col:
            self.skill_sort_reverse = not self.skill_sort_reverse
        else:
            self.skill_sort_column = col
            self.skill_sort_reverse = False
        self._update_skills_view()

    def _sort_inventory_column(self, col):
        """Handles sorting of the inventory treeview when a column header is clicked."""
        if self.inventory_sort_column == col:
            self.inventory_sort_reverse = not self.inventory_sort_reverse
        else:
            self.inventory_sort_column = col
            self.inventory_sort_reverse = False
        self._update_inventory_views()
        
    def _on_skill_search(self, *args):
        self._update_skills_view()

    def _on_inventory_search(self, *args):
        self._update_inventory_views()

    def _add_character(self):
        new_name = simpledialog.askstring("Add New Character", "Enter the name for the new character:", parent=self.root)
        if new_name and new_name.strip():
            if new_name in self.characters:
                messagebox.showwarning("Name Exists", f"A character named '{new_name}' already exists.")
                return
            self._sync_ui_to_character()
            self.characters[new_name] = Character(name=new_name)
            self.active_character_name = new_name
            self._update_all_views()
        elif new_name is not None:
            messagebox.showerror("Invalid Name", "Character name cannot be empty.")

    def _rename_character(self):
        old_name = self.active_character_name
        new_name = simpledialog.askstring("Rename Character", f"Enter the new name for '{old_name}':", parent=self.root)
        if new_name and new_name.strip():
            if new_name in self.characters and new_name != old_name:
                messagebox.showwarning("Name Exists", f"A character named '{new_name}' already exists.")
                return
            self.current_character.name = new_name
            self.characters[new_name] = self.characters.pop(old_name)
            self.active_character_name = new_name
            self._update_all_views()
        elif new_name is not None:
            messagebox.showerror("Invalid Name", "Character name cannot be empty.")

    def _delete_character(self):
        if len(self.characters) <= 1:
            messagebox.showerror("Action Forbidden", "You cannot delete the last character.")
            return
        
        char_to_delete = self.active_character_name
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete '{char_to_delete}'?"):
            del self.characters[char_to_delete]
            self.active_character_name = list(self.characters.keys())[0]
            self._update_all_views()

    def _export_character(self):
        if not self.current_character:
            return

        char = self.current_character
        self._sync_ui_to_character() # Ensure notes are up-to-date before exporting

        # Suggest a filename and open the save dialog
        default_filename = f"{char.name.replace(' ', '_')}_sheet.md"
        filepath = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            parent=self.root,
            title="Export Character Sheet"
        )

        if not filepath:
            return # User cancelled the dialog

        # Build the markdown content string
        content = []
        content.append(f"# Character Sheet: {char.name}\n")

        # Status Section
        content.append("## Status")
        content.append(f"- **Level:** {char.level}")
        next_exp = char.get_exp_for_next_level(char.level)
        exp_str = f"{char.exp} / {next_exp}" if next_exp != float('inf') else "MAX"
        content.append(f"- **Experience:** {exp_str}")
        content.append(f"- **Health:** {char.get_health()}")
        content.append(f"- **Mana:** {char.get_mana()}")
        content.append("\n---\n")

        # Attributes Section
        content.append("## Attributes")
        content.append("| Attribute    | Base | Total | Modifier |")
        content.append("|--------------|------|-------|----------|")
        for attr in CORE_ATTRIBUTES:
            base = char.attributes.get(attr, 10)
            total = char.get_total_attribute(attr)
            mod = char.get_attribute_modifier(attr)
            content.append(f"| {attr:<12} | {base:<4} | {total:<5} | {mod:+<8} |")
        content.append("\n---\n")

        # Skills Section
        if char.skills:
            content.append("## Skills")
            content.append("| Skill        | Level | Experience |")
            content.append("|--------------|-------|------------|")
            for skill in sorted(char.skills, key=lambda s: s['name']):
                skill_next_exp = char.get_exp_for_next_level(skill['level'])
                skill_exp_str = f"{skill['exp']}/{skill_next_exp}" if skill_next_exp != float('inf') else "MAX"
                content.append(f"| {skill['name']:<12} | {skill['level']:<5} | {skill_exp_str:<10} |")
            content.append("\n---\n")

        # Equipment, Inventory, and Notes sections follow...
        content.append("## Equipment")
        equipped_items = [f"- **{slot}:** {item.name}" for slot, item in char.equipment.items() if item]
        content.append("\n".join(equipped_items) if equipped_items else "_No items equipped._")
        content.append("\n---\n")

        content.append("## Inventory")
        inv_items = [f"- **{item.name} (x{item.quantity})**" + (f": {item.description}" if item.description else "") for item in sorted(char.inventory, key=lambda i: i.name)]
        content.append("\n".join(inv_items) if inv_items else "_Inventory is empty._")
        content.append("\n---\n")

        content.append("## Notes")
        content.append(char.notes.strip() if char.notes.strip() else "_No notes._")

        # Write the content to the selected file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            messagebox.showinfo("Export Successful", f"Character sheet for '{char.name}' has been saved.", parent=self.root)
        except IOError as e:
            messagebox.showerror("Export Error", f"Failed to save file:\n{e}", parent=self.root)

    def _handle_add(self, item_type, dialog_class, collection, update_view_func, factory=None):
        if not self.current_character: return
        dialog = dialog_class(self.root, self.theme, f"Add New {item_type.title()}")
        if dialog.result:
            new_obj = factory(**dialog.result) if factory else dialog.result
            collection.append(new_obj)
            update_view_func()

    def _handle_edit(self, treeview, collection, item_type, dialog_class, update_view_func, factory=None):
        if not self.current_character: return
        selected_iid = treeview.focus()
        if not selected_iid:
            messagebox.showerror("Error", f"Please select an {item_type} to edit.")
            return

        index = int(selected_iid)
        item_to_edit = collection[index]

        # Pass the item to edit with the correct keyword argument
        dialog_kwargs = {item_type: item_to_edit}
        dialog = dialog_class(self.root, self.theme, f"Edit {item_type.title()}", **dialog_kwargs)
        
        if dialog.result:
            updated_obj = factory(**dialog.result) if factory else dialog.result
            collection[index] = updated_obj
            update_view_func()

    def _handle_delete(self, treeview, collection, item_type, update_view_func):
        if not self.current_character: return
        selected_iid = treeview.focus()
        if not selected_iid:
            messagebox.showerror("Error", f"Please select an {item_type} to delete.")
            return

        index = int(selected_iid)
        # Safely get the name for the confirmation dialog
        try:
            item_name = collection[index].name if hasattr(collection[index], 'name') else collection[index]['name']
        except (IndexError, KeyError):
            messagebox.showerror("Error", "Could not find the selected item. It may have been deleted.")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{item_name}'?"):
            del collection[index]
            update_view_func()

    def _apply_main_exp(self):
        if not self.current_character: return
        try:
            amount = self.main_exp_gain.get()
            if amount <= 0: return

            old_level = self.current_character.level
            self.current_character.add_exp(amount)
            self._update_status_view()
            self.main_exp_gain.set(0)

            if self.current_character.level > old_level:
                char_name = self.current_character.name.strip() or "you"
                messagebox.showinfo("Level Up!", f"Congratulations, {char_name}! You are now level {self.current_character.level}!")
        except tk.TclError:
            messagebox.showerror("Input Error", "EXP amount must be a valid number.")

    def _remove_main_exp(self):
        if not self.current_character: return
        try:
            amount = self.main_exp_gain.get()
            if amount <= 0: return

            self.current_character.remove_exp(amount)
            self._update_status_view()
            self.main_exp_gain.set(0)

        except tk.TclError:
            messagebox.showerror("Input Error", "EXP amount must be a valid number.")

    def _add_skill(self):
        self._handle_add("skill", SkillEditorDialog, self.current_character.skills, self._update_skills_view)

    def _edit_skill(self):
        self._handle_edit(self.skill_tree, self.current_character.skills, "skill", SkillEditorDialog, self._update_skills_view)

    def _delete_skill(self):
        self._handle_delete(self.skill_tree, self.current_character.skills, "skill", self._update_skills_view)

    def _apply_exp_to_skill(self):
        if not self.current_character: return
        selected_item = self.skill_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a skill from the list to apply EXP to.")
            return

        try:
            index = int(selected_item)
            amount = self.skill_exp_gain.get()
            if amount <= 0: return

            skill = self.current_character.skills[index]
            leveled_up, new_level = self.current_character.add_skill_exp(index, amount)

            if leveled_up:
                messagebox.showinfo("Skill Level Up!", f"{skill['name']} has reached level {new_level}!")

            self._update_skills_view()
            self.skill_exp_gain.set(0)

        except tk.TclError:
            messagebox.showerror("Input Error", "EXP amount must be a valid number.")
        except IndexError:
            messagebox.showerror("Error", "Could not find the selected skill. It may have been deleted.")

    def _remove_exp_from_skill(self):
        if not self.current_character: return
        selected_item = self.skill_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a skill from the list to remove EXP from.")
            return

        try:
            index = int(selected_item)
            amount = self.skill_exp_gain.get()
            if amount <= 0: return

            self.current_character.remove_skill_exp(index, amount)
            self._update_skills_view()
            self.skill_exp_gain.set(0)

        except tk.TclError:
            messagebox.showerror("Input Error", "EXP amount must be a valid number.")
        except IndexError:
            messagebox.showerror("Error", "Could not find the selected skill. It may have been deleted.")

    def _add_item(self):
        self._handle_add("item", ItemEditorDialog, self.current_character.inventory, self._update_inventory_views, factory=Item)

    def _edit_item(self):
        self._handle_edit(self.inv_tree, self.current_character.inventory, "item", ItemEditorDialog, self._update_inventory_views, factory=Item)

    def _delete_item(self):
        self._handle_delete(self.inv_tree, self.current_character.inventory, "item", self._update_inventory_views)

    def _equip_item(self):
        if not self.current_character: return
        selected_item_iid = self.inv_tree.focus()
        if not selected_item_iid:
            messagebox.showerror("Error", "Please select an item from the inventory to equip.")
            return

        index = int(selected_item_iid)
        item = self.current_character.inventory[index]

        slot_to_fill = None
        if item.item_type in ["Weapon", "Shield", "Helmet", "Chestplate", "Leggings", "Boots", "Amulet"]:
            slot_to_fill = item.item_type
        elif item.item_type == "Ring":
            if not self.current_character.equipment["Ring 1"]:
                slot_to_fill = "Ring 1"
            elif not self.current_character.equipment["Ring 2"]:
                slot_to_fill = "Ring 2"
            else:
                choice = simpledialog.askstring("Choose Slot", "Both ring slots are full. Replace Ring 1 or Ring 2? (1/2)", parent=self.root)
                if choice == "1": slot_to_fill = "Ring 1"
                elif choice == "2": slot_to_fill = "Ring 2"
                else: return
        else:
            messagebox.showwarning("Cannot Equip", f"Items of type '{item.item_type}' cannot be equipped.")
            return

        currently_equipped = self.current_character.equipment.get(slot_to_fill)
        if currently_equipped:
            if not messagebox.askyesno("Replace Item?", f"The {slot_to_fill} slot is already equipped with '{currently_equipped.name}'.\nDo you want to replace it? The old item will return to your inventory."):
                return
            self.current_character.inventory.append(currently_equipped)

        self.current_character.equipment[slot_to_fill] = item
        del self.current_character.inventory[index]
        self._update_inventory_views()

    def _unequip_item(self):
        if not self.current_character: return
        selected_item_iid = self.equip_tree.focus()
        if not selected_item_iid:
            messagebox.showerror("Error", "Please select an item from the equipment list to unequip.")
            return

        values = self.equip_tree.item(selected_item_iid, 'values')
        slot = values[0]
        
        item_to_unequip = self.current_character.equipment.get(slot)
        if not item_to_unequip:
            messagebox.showerror("Error", "The selected slot is empty.")
            return

        self.current_character.inventory.append(item_to_unequip)
        self.current_character.equipment[slot] = None
        self._update_inventory_views()

    def _sync_ui_to_character(self):
        if self.current_character:
            self.current_character.notes = self.notes_text.get("1.0", tk.END).strip()

    def _on_notes_modified(self, *args):
        if not self.current_character:
            return
        if self.notes_text.edit_modified():
            self.current_character.notes = self.notes_text.get("1.0", tk.END).strip()
            self.notes_text.edit_modified(False)

    def _on_close(self):
        self._sync_ui_to_character()
        self.pm.save(self.characters, self.theme_name, self.active_character_name)
        self.root.destroy()


class AnimatedDialog(tk.Toplevel):
    """A base class for dialogs that fade in and out."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.transient(parent)
        self.grab_set()
        self.alpha = 0
        self.attributes('-alpha', self.alpha)
        self.after(10, self._fade_in)

    def _fade_in(self):
        if self.alpha < 1.0:
            self.alpha = min(self.alpha + 0.1, 1.0)
            self.attributes('-alpha', self.alpha)
            self.after(15, self._fade_in)

    def close(self):
        """Initiates the fade-out animation and then destroys the window."""
        self.grab_release()
        self._fade_out_and_destroy()

    def _fade_out_and_destroy(self):
        if self.alpha > 0.0:
            self.alpha = max(self.alpha - 0.1, 0.0)
            self.attributes('-alpha', self.alpha)
            self.after(15, self._fade_out_and_destroy)
        else:
            self.destroy()

class SkillEditorDialog(AnimatedDialog):
    def __init__(self, parent, theme, title, skill=None):
        super().__init__(parent, bg=theme["BACKGROUND"])
        self.title(title)
        self.geometry("350x180")
        self.skill_name = tk.StringVar(value=skill['name'] if skill else "")
        self.skill_level = tk.IntVar(value=skill['level'] if skill else 1)
        self.skill_exp = tk.IntVar(value=skill['exp'] if skill else 0)
        self.result = None

        self._create_widgets(theme)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window(self)

    def _validate_integer(self, P):
        return str.isdigit(P) or P == ""

    def _create_widgets(self, theme):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill="both", expand=True)

        vcmd = (self.register(self._validate_integer), '%P')

        ttk.Label(frame, text="Skill Name:", font=Themes.FONT_BOLD).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.skill_name, font=Themes.FONT_NORMAL).grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Level:", font=Themes.FONT_BOLD).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.skill_level, font=Themes.FONT_NORMAL, validate='key', validatecommand=vcmd).grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Current EXP:", font=Themes.FONT_BOLD).grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.skill_exp, font=Themes.FONT_NORMAL, validate='key', validatecommand=vcmd).grid(row=2, column=1, sticky="ew", pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side="left", padx=10)

    def _on_ok(self):
        try:
            self.result = {
                "name": self.skill_name.get(),
                "level": self.skill_level.get(),
                "exp": self.skill_exp.get()
            }
            if not self.result["name"].strip():
                messagebox.showerror("Input Error", "Skill name cannot be empty.", parent=self)
                return
            self.close()
        except tk.TclError:
            messagebox.showerror("Input Error", "Level and EXP must be valid numbers.", parent=self)

    def _on_cancel(self):
        self.result = None
        self.close()

class EffectEditorDialog(AnimatedDialog):
    def __init__(self, parent, theme, title, effect=None):
        super().__init__(parent, bg=theme["BACKGROUND"])
        self.title(title)
        self.attribute = tk.StringVar(value=effect[0] if effect else CORE_ATTRIBUTES[0])
        self.value = tk.IntVar(value=effect[1] if effect else 0)
        self.result = None

        self._create_widgets(theme)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window(self)

    def _validate_integer(self, P):
        # Allow negative numbers for effects
        return (P.isdigit() or (P.startswith('-') and P[1:].isdigit()) or P == "" or P == "-")

    def _create_widgets(self, theme):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill="both", expand=True)

        vcmd = (self.register(self._validate_integer), '%P')

        ttk.Label(frame, text="Attribute:", font=Themes.FONT_BOLD).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=self.attribute, values=CORE_ATTRIBUTES, state="readonly").grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Value:", font=Themes.FONT_BOLD).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.value, font=Themes.FONT_NORMAL, validate='key', validatecommand=vcmd).grid(row=1, column=1, sticky="ew", pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side="left", padx=10)

    def _on_ok(self):
        try:
            self.result = (self.attribute.get(), self.value.get())
            # Final check for empty or just "-"
            if str(self.result[1]).strip() in ["", "-"]:
                messagebox.showerror("Input Error", "Value must be a valid number.", parent=self)
                return
            self.close()
        except tk.TclError:
            messagebox.showerror("Input Error", "Value must be a valid number.", parent=self)

    def _on_cancel(self):
        self.result = None
        self.close()

class ItemEditorDialog(AnimatedDialog):
    def __init__(self, parent, theme, title, item=None):
        super().__init__(parent, bg=theme["BACKGROUND"])
        self.title(title)
        self.geometry("450x450") # Adjusted size
        self.theme = theme

        self.item_name = tk.StringVar(value=item.name if item else "")
        self.item_desc = tk.StringVar(value=item.description if item else "")
        self.item_qty = tk.IntVar(value=item.quantity if item else 1)
        self.item_type = tk.StringVar(value=item.item_type if item else ITEM_TYPES[0])
        self.effects = item.effects.copy() if item and item.effects else {}
        self.result = None

        self._create_widgets()
        self._update_effects_list()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window(self)

    def _validate_integer(self, P):
        return str.isdigit(P) or P == ""

    def _create_widgets(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill="both", expand=True)

        # --- Basic Info ---
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill="x", pady=(0, 15))

        vcmd = (self.register(self._validate_integer), '%P')

        ttk.Label(info_frame, text="Item Name:", font=Themes.FONT_BOLD).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(info_frame, textvariable=self.item_name, font=Themes.FONT_NORMAL).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(info_frame, text="Description:", font=Themes.FONT_BOLD).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(info_frame, textvariable=self.item_desc, font=Themes.FONT_NORMAL).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(info_frame, text="Quantity:", font=Themes.FONT_BOLD).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(info_frame, textvariable=self.item_qty, font=Themes.FONT_NORMAL, validate='key', validatecommand=vcmd).grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(info_frame, text="Item Type:", font=Themes.FONT_BOLD).grid(row=3, column=0, sticky="w", pady=2)
        ttk.Combobox(info_frame, textvariable=self.item_type, values=ITEM_TYPES, state="readonly").grid(row=3, column=1, sticky="ew", pady=2)
        info_frame.columnconfigure(1, weight=1)

        # --- Effects ---
        effects_frame = ttk.LabelFrame(frame, text="Effects", padding=10)
        effects_frame.pack(fill="both", expand=True)

        self.effects_tree = ttk.Treeview(effects_frame, columns=("#1", "#2"), show="headings", height=5)
        self.effects_tree.heading("#1", text="Attribute")
        self.effects_tree.heading("#2", text="Value")
        self.effects_tree.column("#1", anchor="w")
        self.effects_tree.column("#2", anchor="center", width=80)
        self.effects_tree.pack(side="left", fill="both", expand=True)

        effects_btn_frame = ttk.Frame(effects_frame)
        effects_btn_frame.pack(side="right", fill="y", padx=(5, 0))
        ttk.Button(effects_btn_frame, text="Add", command=self._add_effect).pack(pady=2)
        ttk.Button(effects_btn_frame, text="Edit", command=self._edit_effect).pack(pady=2)
        ttk.Button(effects_btn_frame, text="Remove", command=self._remove_effect).pack(pady=2)

        # --- Main Buttons ---
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(15, 0))
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side="right")

    def _update_effects_list(self):
        for i in self.effects_tree.get_children():
            self.effects_tree.delete(i)
        for attr, val in sorted(self.effects.items()):
            self.effects_tree.insert("", "end", values=(attr, val))

    def _add_effect(self):
        dialog = EffectEditorDialog(self, self.theme, "Add Effect")
        if dialog.result:
            attr, value = dialog.result
            self.effects[attr] = value
            self._update_effects_list()

    def _edit_effect(self):
        selected_iid = self.effects_tree.focus()
        if not selected_iid:
            return
        attr, value = self.effects_tree.item(selected_iid, 'values')
        dialog = EffectEditorDialog(self, self.theme, "Edit Effect", effect=(attr, int(value)))
        if dialog.result:
            new_attr, new_value = dialog.result
            # Remove old if attribute changed, to prevent duplicates
            if new_attr != attr:
                del self.effects[attr]
            self.effects[new_attr] = new_value
            self._update_effects_list()

    def _remove_effect(self):
        selected_iid = self.effects_tree.focus()
        if not selected_iid:
            return
        attr, _ = self.effects_tree.item(selected_iid, 'values')
        if messagebox.askyesno("Confirm", f"Remove effect for '{attr}'?", parent=self):
            del self.effects[attr]
            self._update_effects_list()

    def _on_ok(self):
        try:
            self.result = {
                "name": self.item_name.get(),
                "description": self.item_desc.get(),
                "quantity": self.item_qty.get(),
                "item_type": self.item_type.get(),
                "effects": self.effects
            }
            if not self.result["name"].strip():
                messagebox.showerror("Input Error", "Item name cannot be empty.", parent=self)
                return
            if self.result["quantity"] < 1:
                messagebox.showerror("Input Error", "Quantity must be at least 1.", parent=self)
                return
            self.close()
        except tk.TclError:
            messagebox.showerror("Input Error", "Quantity must be a valid number.", parent=self)

    def _on_cancel(self):
        self.result = None
        self.close()

if __name__ == '__main__':
    root = tk.Tk()
    app = CharacterTracker(root)
    root.mainloop()
