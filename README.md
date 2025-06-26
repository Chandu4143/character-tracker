Advanced Character Tracker Application ✨
A feature-rich, desktop application for tracking character progression in tabletop RPGs and other game systems. Built with Python and Tkinter, this application focuses on providing a powerful, intuitive, and visually polished user experience. It goes beyond simple stat tracking to offer a dynamic and interactive character management suite.
![Chartrack-ezgif com-video-to-gif-converter](https://github.com/user-attachments/assets/b9696486-b1f2-4ced-b48c-f5a734aa981c)

 ________________________________________
🚀 Key Features
This application is packed with features designed for a seamless and comprehensive tracking experience:
👑 Character & System Management
Multi-Character Support: Manage multiple character profiles within a single session.
Dynamic Theming: Instantly switch between a sleek Dark Mode and a clean Light Mode.
Data Persistence: All characters and settings are automatically saved on close and reloaded on start.
Markdown Export: Export a complete, beautifully formatted character sheet to a .md or .txt file for printing or sharing.
📊 Status & Attributes
Core Stats: Track level, health, mana, and experience points.
Interactive EXP Bars: Visual progress bars for both main level and individual skills show percentage and current/max values.
Dynamic Attribute System: Edit base attributes (Strength, Dexterity, etc.) and see the total values and modifiers update in real-time based on equipped items.
⚔️ Skills
Live Search & Filter: Instantly find skills by name as you type.
Click-to-Sort Columns: Sort the skill list by name, level, or EXP with a single click.
Detailed EXP Management: Add or remove experience from any skill and watch it level up (or down) automatically.
🎒 Inventory & Equipment
Paned View: A resizable split view for a clear overview of equipped items and general inventory.
Dynamic Equipment Logic: Equipping an item automatically updates character attributes. The system correctly handles unique slots and dual slots (e.g., rings).
Interactive Item Details: Click any item in your inventory or equipment list to see its description.
Advanced Item Editor: Create and edit items with custom names, descriptions, quantities, types, and attribute-modifying effects.
✨ Polished User Experience
Context Menus: Right-click on skills or items for quick access to actions like "Edit," "Delete," and "Equip," keeping the UI clean.
Animated Dialogs: All pop-up windows fade in and out smoothly for a modern feel.
Helpful Tooltips: Hover over buttons to see a description of what they do.
Custom Smooth Scrolling: A custom-implemented, eased-out smooth scroll enhances the Notes tab.
________________________________________
🛠️ Technology Stack
•	Language: Python 3
•	UI Framework: Tkinter (from the Python Standard Library)
•	Data Serialization: JSON
No external libraries are required to run this application.
________________________________________
📥 Installation
For Users
The easiest way to get the application is to download the latest release.
Go to the Releases Page.
Under the latest release, click CharacterTracker.exe to download.
Run the downloaded file. No installation is needed!
For Developers
If you want to run the code from the source or contribute:
Clone the repository:
Generated bash
git clone https://github.com/Chandu4143/character-tracker.git
cd character-tracker
Use code with caution.
Bash
Run the application:
Generated bash
python character_tracker_app.py
Use code with caution.
Bash
To build the executable yourself:
Install PyInstaller: pip install pyinstaller
Run the build command:
Generated bash
pyinstaller --onefile --windowed --name "CharacterTracker" --icon="icon.ico" character_tracker_app.py
Use code with caution.
Bash
The final .exe will be in the newly created dist folder.
________________________________________
📖 How to Use
•	Character Management: Use the dropdown and buttons at the top of the window to switch, add, rename, delete, or export character profiles.
•	Attributes & Status: View your character's core stats on the Status tab. On the Attributes tab, click and edit the "Base" value for any attribute; the "Total" and "Modifier" will update automatically based on your gear.
•	Skills: Use the Add Skill button to create a new skill. Select a skill from the list to see its progress and add/remove EXP using the controls below. Right-click a skill to Edit or Delete it.
•	Inventory: Right-click an item in your inventory to Equip, Edit, or Delete it. Right-click an equipped item to Unequip it. Use the "Add Item" button to open the powerful item editor.
________________________________________
🌟 Future Development
This project has a solid foundation for future expansion. Possible next steps include:
•	Quest Log / Journal Tab: A dedicated section to track active and completed quests.
•	Undo/Redo System: Implement a command pattern to allow undoing actions like adding EXP or deleting items.
•	Configurable Rulesets: Allow users to define their own attributes, equipment slots, and EXP formulas via external JSON files to support any game system.
________________________________________
📄 License
This project is licensed under the MIT License. See the LICENSE file for details.

