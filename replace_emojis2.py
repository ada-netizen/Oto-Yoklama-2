import io

emoji_map = {
    '📋': '<i data-lucide="clipboard" width="16" height="16"></i>',
    '📅': '<i data-lucide="calendar" width="16" height="16"></i>',
    '🧠': '<i data-lucide="brain" width="16" height="16"></i>',
    '⬇️': '<i data-lucide="download" width="16" height="16"></i>',
    '📄': '<i data-lucide="file-text" width="16" height="16"></i>',
    '📊': '<i data-lucide="bar-chart" width="16" height="16"></i>',
    '✖': '<i data-lucide="x" width="16" height="16"></i>',
    '💾': '<i data-lucide="save" width="16" height="16"></i>',
    '🖋️': '<i data-lucide="pen-tool" width="16" height="16"></i>',
    '⚙️': '<i data-lucide="settings" width=\"16\" height=\"16\"></i>',
    '💡': '<i data-lucide="lightbulb" width="16" height="16"></i>',
    '🌙': '<i data-lucide="moon" width="16" height="16"></i>',
    '⭐': '<i data-lucide="sun" width="16" height="16"></i>',
    '📥': '<i data-lucide="download-cloud" width="16" height="16"></i>',
    '🗑️': '<i data-lucide="trash-2" width="16" height="16"></i>',
    '✉️': '<i data-lucide="mail" width="16" height="16"></i>',
    '🏫': '<i data-lucide="school" width="16" height="16"></i>',
    '👥': '<i data-lucide="users" width="16" height="16"></i>',
    '🔄': '<i data-lucide="refresh-cw" width="16" height="16"></i>',
    '📑': '<i data-lucide="file-stack" width="16" height="16"></i>',
    '👨‍🎓': '<i data-lucide="graduation-cap" width="16" height="16"></i>',
    '👔': '<i data-lucide="users" width="16" height="16"></i>',
    '🗑': '<i data-lucide="trash-2" width="16" height="16"></i>',
    '➕': '<i data-lucide="plus" width="16" height="16"></i>',
    '🔍': '<i data-lucide="search" width="16" height="16"></i>',
    '✔️': '<i data-lucide="check" width="16" height="16"></i>',
    '⛭': '<i data-lucide="settings" width="32" height="32"></i>',
    '⬅': '<i data-lucide="arrow-left" width="16" height="16"></i>',
    '👤': '<i data-lucide="user" width="16" height="16"></i>'
}

with io.open('app.js', 'r', encoding='utf-8') as f:
    content = f.read()

for emoji, lucide in emoji_map.items():
    content = content.replace(emoji, lucide)

with io.open('app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print('Emojis replaced in app.js.')
