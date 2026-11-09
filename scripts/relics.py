"""Animate real, locally stored mod images without redrawing their textures."""

import base64
from functools import lru_cache
import hashlib
from html import escape
import json
from pathlib import Path

from svg import arrive, loop

ASSET_ROOT = Path(__file__).resolve().parents[1]/'profile/assets/originals'


@lru_cache(maxsize=1)
def image_defs():
    manifest=json.loads((ASSET_ROOT/'sources.json').read_text(encoding='utf-8'))
    parts=[]
    for name,spec in manifest.items():
        data=(ASSET_ROOT/f'{name}.png').read_bytes()
        if hashlib.sha256(data).hexdigest()!=spec['png_sha256']:
            raise ValueError(f'Image differs from its source manifest: {name}')
        width,height=spec['size']
        mode='pixelated' if max(width,height)<=32 else 'auto'
        parts.append(f'<symbol id="image-{name}" viewBox="0 0 {width} {height}">'
                     f'<image width="{width}" height="{height}" style="image-rendering:{mode}" '
                     f'href="data:image/png;base64,{base64.b64encode(data).decode()}"/>'
                     f'<desc>{escape(spec["description"])}</desc></symbol>')
    return ''.join(parts)


def picture(name,x,y,width,height=None):
    height=width if height is None else height
    return f'<use href="#image-{name}" x="{x}" y="{y}" width="{width}" height="{height}" class="source-image"/>'


def float_image(content, amount=7):
    return loop(content,['0 0',f'0 {-amount}','0 0','0 0'],times=[0,.25,.5,1])


def thaumcraft():
    jar=arrive(picture('warded-jar',-115,-27,113),'0 50')
    lens=arrive(float_image(picture('thaumometer',-56,-105,190),10),'65 -25')
    return jar+lens


def industrialcraft():
    return arrive(float_image(picture('macerator',-107,-116,214)),'-60 45')


def applied():
    return arrive(float_image(picture('me-drive',-101,-110,202)),'50 45')


def buildcraft():
    return arrive(float_image(picture('quarry',-108,-118,216)),'0 65')


def forestry():
    return arrive(float_image(picture('apiary',-112,-113,224)),'-45 50')


def lava():
    return arrive(float_image(picture('lavacraft-logo',-153,-94,306,187),5),'45 35')


RELICS = (
    ('thaumcraft','Thaumcraft 4','ТАУМОМЕТР И ЭССЕНЦИЯ','#c6a5dc',thaumcraft),
    ('industrialcraft','IndustrialCraft 2','ДРОБИТЕЛЬ / MACERATOR','#a9c4b6',industrialcraft),
    ('applied','Applied Energistics','ОРИГИНАЛЬНЫЙ AE / ME DRIVE','#a0c5d4',applied),
    ('buildcraft','BuildCraft','КАРЬЕР / QUARRY','#d9bd80',buildcraft),
    ('forestry','Forestry','ПАСЕКА / APIARY','#b8c78c',forestry),
    ('lava','LavaCraft','LAVACRAFT.RU / LAVAMOD','#e0a779',lava),
)
