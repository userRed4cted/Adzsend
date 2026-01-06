#!/usr/bin/env python3
"""Fix various styling issues in settings.html"""

# Read the file
with open('templates/settings.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix copy.png color - change green filter to grayscale to match the grey text (#717688)
# The adzsend id text is color: #717688 which is a grey color
# Change from green filter to a grey/transparent filter
old_copy_filter = 'filter: sepia(1) saturate(5) hue-rotate(130deg) brightness(0.9)'
new_copy_filter = 'filter: brightness(0.5) opacity(0.7)'
content = content.replace(old_copy_filter, new_copy_filter)

# 2. Fix Account and Adzsend ID labels - change from setting-label (white, large) to usage-label style (grey, smaller)
# Account label at line 550
old_account_label = '<div class="setting-label">Account</div>'
new_account_label = '<div class="usage-label">Account</div>'
content = content.replace(old_account_label, new_account_label)

# Adzsend ID label at line 562
old_adzsend_label = '<div class="setting-label">Adzsend ID</div>'
new_adzsend_label = '<div class="usage-label">Adzsend ID</div>'
content = content.replace(old_adzsend_label, new_adzsend_label)

# 3. Fix owner tag in settings teams - match the team-management style
# Old style: <div style="color: #15d8bc; font-size: 0.8rem; font-weight: 500;">Owner</div>
# New style: <span style="background: linear-gradient(to bottom, #15d8bc, #006e59); color: #121215; font-size: 0.6rem; padding: 0.15rem 0.4rem; border-radius: 3px; margin-left: 0.5rem; font-weight: 500;">Owner</span>
old_owner_tag = '<div style="color: #15d8bc; font-size: 0.8rem; font-weight: 500;">Owner</div>'
new_owner_tag = '<span style="background: linear-gradient(to bottom, #15d8bc, #006e59); color: #121215; font-size: 0.6rem; padding: 0.15rem 0.4rem; border-radius: 3px; font-weight: 500; line-height: 1.2;">Owner</span>'
content = content.replace(old_owner_tag, new_owner_tag)

# 4. Fix billing buttons rescaling - add padding to compensate for border differences
# The issue is when active has no border but inactive has 2px border
# Fix by giving active button a 2px transparent border to maintain consistent sizing
old_plan_btn = '''<button class="billing-view-btn active" data-view="plan-info" style="flex: 1; padding: 0.5rem 1rem; background: linear-gradient(to bottom, #15d8bc, #006e59); border: none; border-radius: 6px 0 0 6px; color: #121215; font-weight: 500; cursor: pointer; transition: all 0.2s ease; box-sizing: border-box; position: relative; z-index: 1;">Plan Information</button>'''
new_plan_btn = '''<button class="billing-view-btn active" data-view="plan-info" style="flex: 1; padding: 0.5rem 1rem; background: linear-gradient(to bottom, #15d8bc, #006e59); border: 2px solid transparent; border-radius: 6px 0 0 6px; color: #121215; font-weight: 500; cursor: pointer; transition: all 0.2s ease; box-sizing: border-box; position: relative; z-index: 1;">Plan Information</button>'''
content = content.replace(old_plan_btn, new_plan_btn)

# Also fix the JavaScript that toggles the buttons
old_border_none = "b.style.border = 'none';"
new_border_transparent = "b.style.border = '2px solid transparent';"
content = content.replace(old_border_none, new_border_transparent)

# Write the file back
with open('templates/settings.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed settings.html:")
print("1. Changed copy.png filter from green to grey")
print("2. Changed Account label to usage-label style")
print("3. Changed Adzsend ID label to usage-label style")
print("4. Updated Owner tag to match team-management gradient style")
print("5. Fixed billing buttons border consistency")
