#!/usr/bin/env python3
"""Fix owner tag cropping in team-management.html"""

# Read the file
with open('templates/team-management.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The owner tag is getting cropped at the bottom - add line-height to fix
old_owner_tag = '<span style="background: linear-gradient(to bottom, #15d8bc, #006e59); color: #121215; font-size: 0.6rem; padding: 0.15rem 0.4rem; border-radius: 3px; margin-left: 0.5rem; font-weight: 500;">Owner</span>'
new_owner_tag = '<span style="background: linear-gradient(to bottom, #15d8bc, #006e59); color: #121215; font-size: 0.6rem; padding: 0.2rem 0.4rem; border-radius: 3px; margin-left: 0.5rem; font-weight: 500; line-height: 1.2; display: inline-block; vertical-align: middle;">Owner</span>'
content = content.replace(old_owner_tag, new_owner_tag)

# Write the file back
with open('templates/team-management.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed team-management.html:")
print("- Added line-height, display: inline-block, and vertical-align to owner tag")
print("- Increased vertical padding slightly for better visibility")
