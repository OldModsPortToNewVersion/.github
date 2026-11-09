"""Import explicitly sourced wiki sprites and the official LavaCraft logo.

Requires Pillow only for cropping PNG sprite sheets. Network access is confined
to this one-time importer; build_cover.py embeds the resulting local PNG files.
"""

import hashlib
import io
import json
from pathlib import Path
import urllib.request

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CDN = 'https://static.wikia.nocookie.net/ftb_gamepedia/images/'
ASSETS = {
    'thaumometer': {
        'url':'https://static.wikia.nocookie.net/thaumcraft-4/images/f/f2/Thaumometer-1-.png/revision/latest?cb=20140129171023',
        'polygon':[[195,3],[561,7],[742,326],[568,639],[198,639],[4,314]],
        'trim':True, 'clear_hidden_rgb':True, 'page':'https://thaumcraft-4.fandom.com/wiki/Thaumometer',
        'description':'Thaumcraft 4 in-game thaumometer image uploaded in January 2014. Background removed along its outer hexagon.',
        'attribution':'Thaumcraft / Azanor; image hosted by Thaumcraft 4 Wiki contributors.',
    },
    'warded-jar': {
        'url': CDN+'f/f0/Tilesheet_TC4_32_0.png/revision/latest?cb=20211227225209',
        'crop':[192,640,224,672], 'page':'https://ftb.fandom.com/wiki/Warded_Jar_(Thaumcraft_4)',
        'description':'Warded Jar from Thaumcraft 4.',
        'attribution':'Thaumcraft / Azanor; sprite hosted by Feed The Beast Wiki contributors.',
    },
    'macerator': {
        'url':CDN+'2/2b/Block_Macerator.png/revision/latest?cb=20151224165243',
        'page':'https://ftb.fandom.com/wiki/Macerator_(IndustrialCraft_2)',
        'description':'IndustrialCraft 2 Macerator render, source image uploaded in 2015; exact mod build unspecified.',
        'attribution':'IndustrialCraft 2 team; render hosted by Feed The Beast Wiki contributors.',
    },
    'me-drive': {
        'url':'https://static.wikia.nocookie.net/feed-the-beast/images/2/2d/ME_Drive_Block2.png/revision/latest?cb=20130606154543',
        'polygon':[[740,375],[891,309],[1033,366],[1029,477],[1091,512],[1089,562],[1057,594],[999,564],[899,620],[767,529]],
        'trim':True,'clear_hidden_rgb':True,'page':'https://feed-the-beast.fandom.com/wiki/File:ME_Drive_Block2.png',
        'description':'ME Drive from the original Applied Energistics, isolated from an in-game screenshot uploaded in June 2013; not Applied Energistics 2.',
        'attribution':'Applied Energistics / AlgorithmX2; screenshot hosted by Feed The Beast Wiki contributors.',
    },
    'quarry': {
        'url':CDN+'2/28/Quarry.png/revision/latest?cb=20200201134828',
        'page':'https://ftb.fandom.com/wiki/Quarry',
        'description':'BuildCraft Quarry render; source article describes the RF-powered generation. Exact build unspecified.',
        'attribution':'BuildCraft team; render hosted by Feed The Beast Wiki contributors.',
    },
    'apiary': {
        'url':'https://static.wikia.nocookie.net/feed-the-beast/images/1/14/Apiary.png/revision/latest?cb=20130214161249',
        'page':'https://feed-the-beast.fandom.com/wiki/File:Apiary.png',
        'description':'Forestry Apiary render uploaded in February 2013; source page does not specify an exact mod build.',
        'attribution':'Forestry / SirSengir and contributors; render hosted by Feed The Beast Wiki contributors.',
    },
    'lavacraft-logo': {
        'url':'https://lavacraft.ru/imgNew/logo.png', 'page':'https://lavacraft.ru/',
        'description':'Official LavaCraft.ru website logo, selected after the user identified this server.',
        'attribution':'LavaCraft.ru. This is the server logo, not an invented LavaMod block.',
    },
}


def main():
    output=ROOT/'profile/assets/originals'
    output.mkdir(parents=True,exist_ok=True)
    manifest_path=output/'sources.json'
    previous=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    downloaded={}
    manifest={}
    pngs={}
    for name,spec in ASSETS.items():
        local=output/f'{name}.png'
        if name in previous and all(previous[name].get(k)==v for k,v in spec.items()) and local.exists():
            if hashlib.sha256(local.read_bytes()).hexdigest()!=previous[name]['png_sha256']:
                raise ValueError(f'{name}: local image was changed; review it before importing')
            manifest[name]=previous[name]
            print(name,'verified local copy')
            continue
        url=spec['url']
        if url not in downloaded:
            request=urllib.request.Request(url,headers={'User-Agent':'OldModsProfile/1.0'})
            with urllib.request.urlopen(request,timeout=120) as response:
                downloaded[url]=response.read()
        data=downloaded[url]
        image=Image.open(io.BytesIO(data)).convert('RGBA')
        original_size=image.size
        if 'polygon' in spec:
            mask=Image.new('L',image.size,0)
            ImageDraw.Draw(mask).polygon([tuple(point) for point in spec['polygon']],fill=255)
            image.putalpha(mask)
        if 'crop' in spec:
            x1,y1,x2,y2=spec['crop']
            if not (0<=x1<x2<=image.width and 0<=y1<y2<=image.height):
                raise ValueError(f'{name}: crop is outside the source sheet')
            image=image.crop((x1,y1,x2,y2))
        if image.getchannel('A').getbbox() is None:
            raise ValueError(f'{name}: empty image')
        if spec.get('trim'):
            image=image.crop(image.getchannel('A').getbbox())
        if spec.get('clear_hidden_rgb'):
            image=Image.alpha_composite(Image.new('RGBA',image.size,(0,0,0,0)),image)
        encoded=io.BytesIO()
        image.save(encoded,format='PNG',optimize=True)
        png=encoded.getvalue()
        pngs[name]=png
        manifest[name]={**spec,'source_sha256':hashlib.sha256(data).hexdigest(),
                        'png_sha256':hashlib.sha256(png).hexdigest(),
                        'source_size':original_size,'size':image.size}
        print(name,original_size,'->',image.size,len(png),'bytes')
    for name,png in pngs.items():
        (output/f'{name}.png').write_bytes(png)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
