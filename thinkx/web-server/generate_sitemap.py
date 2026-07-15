languages = ['en', 'ja']  # Add more languages as needed

sitemap_entries = []
base_url = "https://thinkxinc.com"

# Pages and their priorities
pages = [
    ("/", 1.0),
    ("/products/Quantz-Voice-AI-OS", 1.0),
    ("/mission", 0.8),
    ("/philosophy", 0.8),
    ("/about", 0.8),
    ("/blognews", 0.7),
    ("/apply/regular", 0.7),
    ("/history", 0.6),
    ("/apply/intern", 0.6),
    ("/inquiry/product", 0.6),
    ("/apply/collaborator", 0.5),
    ("/ir/investor", 0.5),
    ("/inquiry/collaboration", 0.5),
    ("/inquiry/others", 0.5)
]

# Generate sitemap entries for each language
for lang in languages:
    for page, priority in pages:
        sitemap_entries.append((f"    <url>\n        <loc>{base_url}/{lang}{page}</loc>\n        <priority>{priority}</priority>\n    </url>", priority))

# External Quantz product page (special case, handle outside the loop if language specific)
for lang in languages:
    sitemap_entries.append((f"    <url>\n        <loc>https://quantz.thinkxinc.com/{lang}</loc>\n        <priority>1.0</priority>\n    </url>", 1.0))

# Sort entries by priority, highest first
sitemap_entries.sort(key=lambda x: x[1], reverse=True)

# Combine entries into final XML content
sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(entry[0] for entry in sitemap_entries)}
</urlset>
"""

# Write to sitemap.xml
with open("sitemap.xml", "w") as file:
    file.write(sitemap_content)

print("Sitemap generated successfully.")
