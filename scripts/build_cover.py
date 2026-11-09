#!/usr/bin/env python3
"""Build the legacy chapter of the OldModsPortToNewVersion organization profile."""

from pathlib import Path

from relics import RELICS, image_defs
from svg import arrive, serialize, text

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1200, 1120
PALETTES = {
    'dark': {'bg':'#121417','panel':'#1e2125','fg':'#f1ebdf','muted':'#a9a69f','line':'#36383a','accent':'#dabc88','plinth':'#292c30','edge':'#181b1e'},
    'light': {'bg':'#f0eee7','panel':'#fcfaf3','fg':'#302e2a','muted':'#69655c','line':'#d9d4c7','accent':'#846334','plinth':'#d4cfc2','edge':'#b3afa4'},
}


def defs(p):
    return f'''
    <linearGradient id="background" x2=".6" y2="1"><stop stop-color="{p['panel']}"/><stop offset="1" stop-color="{p['bg']}"/></linearGradient>
    <radialGradient id="warm"><stop stop-color="#c3a374" stop-opacity=".10"/><stop offset="1" stop-color="#c3a374" stop-opacity="0"/></radialGradient>
    <linearGradient id="divider"><stop stop-color="{p['line']}" stop-opacity="0"/><stop offset=".2" stop-color="{p['line']}"/><stop offset=".8" stop-color="{p['line']}"/><stop offset="1" stop-color="{p['line']}" stop-opacity="0"/></linearGradient>
    <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".65" fill="{p['fg']}" opacity=".055"/></pattern>
    <clipPath id="frame"><rect x="1" y="1" width="1198" height="{HEIGHT-2}" rx="26"/></clipPath>
    <clipPath id="relic-frame" clipPathUnits="userSpaceOnUse"><rect x="-172" y="-125" width="344" height="288"/></clipPath>
    <filter id="shadow" x="-40%" y="-100%" width="180%" height="300%"><feGaussianBlur stdDeviation="10"/></filter>
    '''


def styles():
    return '''
    text{font-family:'Segoe UI',Arial,sans-serif}
    .mono{font-family:Consolas,'Courier New',monospace}
    .headline{font-weight:750;letter-spacing:-4px}
    .static,.mobile{display:none}
    .relic-name{font-weight:600;letter-spacing:-.6px}
    @media(max-width:600px){
      .desktop{display:none}.mobile{display:inline}
      .relic-name{font-size:39px}
      .relic-note{display:none}
      .relic{transform:scale(.95)}
      .footer{font-size:31px}
    }
    @media(prefers-reduced-motion:reduce){.animated{display:none}.static{display:inline}}
    '''


def heading(p):
    eyebrow = text(56,56,'OLD MODS / NEW CHAPTER',17,p['muted'],class_='mono',letter_spacing=2)
    eyebrow += text(1144,56,'01 — LEGACY',17,p['accent'],class_='mono',text_anchor='end',letter_spacing=1)
    titles = text(51,144,'Старые моды.',91,p['fg'],class_='headline')
    titles += text(51,240,'Новые истории.',91,p['accent'],class_='headline')
    aside = (text(786,129,'Возвращаем легенды',27,p['fg'])
             +text(786,167,'на новые версии Minecraft.',27,p['fg'])
             +text(786,213,'Для твоей следующей сборки.',22,p['muted']))
    desktop = '<g class="desktop">'+arrive(aside,'25 0',.6)+'</g>'
    mobile = '<g class="mobile">'+arrive(text(56,297,'Любимые моды — для новых сборок.',41,p['muted']),'0 16',.55)+'</g>'
    return arrive(eyebrow,'0 12',.12,.8)+arrive(titles,'0 35',.22,1.4)+desktop+mobile


def pedestal(p, accent):
    return f'''
    <ellipse cy="102" rx="119" ry="15" fill="#000" opacity=".18" filter="url(#shadow)"/>
    <path d="M-133 76 0 11 133 76 0 141Z" fill="{p['plinth']}"/>
    <path d="M-133 76v12L0 153V141Z M0 141l133-65v12L0 153Z" fill="{p['edge']}"/>
    <path d="M-133 76 0 141 133 76" fill="none" stroke="{accent}" stroke-opacity=".24"/>
    '''


def gallery(p):
    scenes = []
    for index,(name,label,note,accent,draw) in enumerate(RELICS):
        x = 218+(index%3)*382
        y = 432+(index//3)*373
        art = '<g class="relic" clip-path="url(#relic-frame)">'+pedestal(p,accent)+'<g transform="translate(0 -7)">'+draw()+'</g></g>'
        content = arrive(art,'0 24',.35,1.6)
        content += arrive(text(0,187,label,30,p['fg'],class_='relic-name',text_anchor='middle'),'0 14',.65,1)
        content += arrive(text(0,216,note,12,p['muted'],class_='relic-note mono',text_anchor='middle',letter_spacing=1.4),'0 10',.75,1)
        # Local coordinates keep animations independent of gallery placement.
        scenes.append(f'<g id="relic-{name}" class="exhibit" transform="translate({x} {y})">{content}</g>')
    return ''.join(scenes)


def build(theme):
    p = PALETTES[theme]
    background = f'''<rect x="1" y="1" width="1198" height="{HEIGHT-2}" rx="26" fill="url(#background)" stroke="{p['line']}"/>
    <ellipse cx="210" cy="425" rx="510" ry="470" fill="url(#warm)"/>
    <rect x="16" y="318" width="1168" height="730" fill="url(#dots)"/>
    <path d="M64 666H1136" stroke="url(#divider)"/>
    <path d="M408 325V1047M792 325V1047" stroke="{p['line']}" opacity=".5"/>
    <path d="M56 1062H1144" stroke="{p['line']}"/>'''
    footer = text(56,1098,'СОХРАНЯЕМ ХАРАКТЕР. ПРОДОЛЖАЕМ ИСТОРИЮ.',16,p['muted'],class_='footer mono',letter_spacing=1)
    footer += '<g class="desktop">'+text(1144,1098,'MINECRAFT MODDING',14,p['accent'],class_='mono',text_anchor='end',letter_spacing=1)+'</g>'
    return serialize(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
    <title id="title">Старые моды. Новые истории.</title>
    <desc id="desc">OldModsPortToNewVersion — перенос легендарных модов на новые версии Minecraft для современных сборок. Реальные изображения Thaumcraft 4, IndustrialCraft 2, оригинального Applied Energistics, BuildCraft, Forestry и официальный логотип LavaCraft.ru.</desc>
    <defs>{defs(p)}{image_defs()}</defs><style>{styles()}</style>
    <g id="scene"><g clip-path="url(#frame)">{background}{heading(p)}{gallery(p)}{arrive(footer,'0 10',.8,1)}</g></g>
    </svg>''')


def main():
    output = ROOT/'profile/assets'
    output.mkdir(parents=True,exist_ok=True)
    for theme in PALETTES:
        path = output/f'legacy-{theme}.svg'
        path.write_text(build(theme),encoding='utf-8',newline='\n')
        print(path.relative_to(ROOT))


if __name__ == '__main__':
    main()
