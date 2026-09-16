import re

def asyncify_api(content):
    # Convert route defs to async def
    content = re.sub(r'(@app\.(get|post|put|delete)\(.*\)\n)def ', r'\1async def ', content)
    
    # db.cursor.execute(...) -> await db.execute(...) is hard without context because db might be aiosqlite connection now.
    # Actually, aiosqlite uses `async with db.execute(...)` or `await db.execute(...)`.
    # Let's not fully migrate api.py automatically as it's too error prone.
    return content

# I will write a simple rollback for veritabani if it fails, or I can inform the user that I've prepared the groundwork.
