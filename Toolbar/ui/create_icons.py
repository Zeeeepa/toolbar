import os

def create_svg_icon(filename, content):
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Created {filename}")

# Create icons directory if it doesn't exist
if not os.path.exists("icons"):
    os.makedirs("icons")

# Add icon
add_icon = '''<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
  <circle cx="16" cy="16" r="14" fill="none" stroke="#00FF00" stroke-width="2"/>
  <line x1="16" y1="8" x2="16" y2="24" stroke="#00FF00" stroke-width="2"/>
  <line x1="8" y1="16" x2="24" y2="16" stroke="#00FF00" stroke-width="2"/>
</svg>'''

# Exit icon
exit_icon = '''<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
  <circle cx="16" cy="16" r="14" fill="none" stroke="#FF0000" stroke-width="2"/>
  <line x1="10" y1="10" x2="22" y2="22" stroke="#FF0000" stroke-width="2"/>
  <line x1="22" y1="10" x2="10" y2="22" stroke="#FF0000" stroke-width="2"/>
</svg>'''

# Python script icon
python_icon = '''<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
  <rect x="4" y="4" width="24" height="24" rx="2" fill="none" stroke="#3776AB" stroke-width="2"/>
  <text x="10" y="22" font-family="Arial" font-size="18" fill="#3776AB">P</text>
</svg>'''

# Batch script icon
batch_icon = '''<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
  <rect x="4" y="4" width="24" height="24" rx="2" fill="none" stroke="#666666" stroke-width="2"/>
  <text x="10" y="22" font-family="Arial" font-size="18" fill="#666666">B</text>
</svg>'''

create_svg_icon("icons/add.svg", add_icon)
create_svg_icon("icons/exit.svg", exit_icon)
create_svg_icon("icons/python.svg", python_icon)
create_svg_icon("icons/batch.svg", batch_icon)

print("Icons created successfully. Place them in the 'icons' folder.") 