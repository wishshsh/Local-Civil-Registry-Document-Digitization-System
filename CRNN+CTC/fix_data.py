import os, json, random
from PIL import Image, ImageDraw, ImageFont

FIRST_NAMES = ['Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Carlos', 'Luz']
LAST_NAMES  = ['Dela Cruz', 'Santos', 'Reyes', 'Garcia', 'Torres', 'Flores']
PLACES      = ['Tarlac City', 'Manila', 'Quezon City', 'Cebu City', 'Davao City']
DATES       = ['01/15/1990', '03/22/1985', '07/04/2000', '11/30/1995', '05/18/1988']

def random_text():
    name = random.choice(FIRST_NAMES) + ' ' + random.choice(LAST_NAMES)
    return random.choice([name, random.choice(DATES), random.choice(PLACES)])

def create_image(text):
    img = Image.new('RGB', (200, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 20)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    x = max((200 - (bbox[2] - bbox[0])) // 2, 2)
    y = max((64  - (bbox[3] - bbox[1])) // 2, 2)
    draw.text((x, y), text, fill=(0, 0, 0), font=font)
    return img

for split in ['train', 'val']:
    count = 50 if split == 'train' else 20
    entries = []
    for form in ['form1a', 'form2a']:
        for i in range(count):
            text = random_text()
            fname = f'{form}_{i+1:04d}.jpg'
            path = f'data/{split}/{form}/{fname}'
            create_image(text).save(path)
            entries.append({'image_path': f'{form}/{fname}', 'text': text})
    with open(f'data/{split}_annotations.json', 'w') as f:
        json.dump(entries, f, indent=2)
    print(f'{split} done!')

print('All images regenerated!')