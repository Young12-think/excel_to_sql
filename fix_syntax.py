import sys

def fix():
    filepath = r"d:\timbangan system\python\excelmysql\app.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find and replace all instances of:
    # {self.db_config.get("host", "127.0.0.1")} inside f-strings using double quotes
    
    # Just replace them with single quotes inside:
    content = content.replace('{self.db_config.get("host", "127.0.0.1")}', "{self.db_config.get('host', '127.0.0.1')}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix()
