import os, base64

PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAIUlEQVQoU2NkYGBg+M+AB0gYGBgGJgYGRkYGQYAAH0nB6OeQ7hSAAAAAElFTkSuQmCC"
)

def create_default_logo():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    path = os.path.join(assets_dir, 'default-logo.png')
    with open(path, 'wb') as f:
        f.write(base64.b64decode(PNG_BASE64))
    return path

if __name__ == '__main__':
    p = create_default_logo()
    print('Created', p)
