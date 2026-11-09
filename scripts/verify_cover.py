"""Render the real cover at desktop/mobile widths, audit geometry and export previews."""

import argparse
import io
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

from build_cover import ROOT, WIDTH, HEIGHT, build
from svg import CYCLE, START


def inline(theme,width):
    root=ET.fromstring(build(theme))
    root.set('width',str(width))
    root.set('height',str(width*HEIGHT/WIDTH))
    return '<style>body{margin:0}svg{display:block}</style>'+ET.tostring(root,encoding='unicode')


def seek(page,time):
    page.evaluate('''async t=>{
      const svg=document.querySelector('svg');svg.pauseAnimations();
      svg.setCurrentTime(1);svg.setCurrentTime(Math.max(t,.001));
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    }''',time)


def image(page):
    return Image.open(io.BytesIO(page.locator('svg').screenshot())).convert('RGB')


def geometry(page):
    return page.locator('#scene').evaluate('''scene=>{
      const inv=scene.getScreenCTM().inverse();
      return [...scene.querySelectorAll('text')].filter(e=>e.getBoundingClientRect().width>0).map(e=>{
        const b=e.getBoundingClientRect(),a=new DOMPoint(b.left,b.top).matrixTransform(inv),z=new DOMPoint(b.right,b.bottom).matrixTransform(inv);
        return {text:e.textContent,x1:a.x,y1:a.y,x2:z.x,y2:z.y};
      });
    }''')


def state(page):
    return page.locator('#scene .detail-loop').evaluate_all('''es=>es.map(e=>{
      const m=e.getCTM();return [m.a,m.b,m.c,m.d,m.e,m.f,Number(getComputedStyle(e).opacity)];
    })''')


def check_label_clearance(page):
    boxes=page.locator('#scene').evaluate('''scene=>{
      const box=e=>{const b=e.getBoundingClientRect();return {x1:b.left,y1:b.top,x2:b.right,y2:b.bottom}};
      return [...scene.querySelectorAll('.exhibit')].map(e=>({
        label:box(e.querySelector('.relic-name')), art:box(e.querySelector('.relic'))
      }));
    }''')
    for top,bottom in zip(boxes[:3],boxes[3:]):
        assert top['label']['y2']+5<bottom['art']['y1'], ('adjacent row overlaps label',top,bottom)


def contact_sheet(frames,path):
    width,height=frames[0][1].size
    sheet=Image.new('RGB',(width*3,(height+28)*2),'#131518')
    draw=ImageDraw.Draw(sheet)
    for i,(time,frame) in enumerate(frames):
        x,y=i%3*width,i//3*(height+28)
        draw.text((x+12,y+7),f'{time}s',fill='white')
        sheet.paste(frame,(x,y+28))
    sheet.save(path)


def check(browser,output):
    report=[]
    for theme in ('dark','light'):
        for width in (1080,358):
            page=browser.new_page(viewport={'width':width,'height':1100},color_scheme=theme)
            page.set_content(inline(theme,width))
            seek(page,2.3)
            image(page).save(output/f'cover-{theme}-{width}.png')
            boxes=geometry(page)
            check_label_clearance(page)
            for box in boxes:
                assert 10<=box['x1']<box['x2']<=WIDTH-10 and 5<=box['y1']<box['y2']<=HEIGHT-8, (theme,width,box)
            for t in (.65,1.2,2.3,4.5,6.8):
                seek(page,t)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            seek(page,START+1.5)
            first=state(page)
            seek(page,START+1.5+5*CYCLE)
            later=state(page)
            assert len(first)==len(later)>5
            assert all(math.isclose(a,b,abs_tol=.001) for r,s in zip(first,later) for a,b in zip(r,s)), 'cycle drift'
            page.emulate_media(reduced_motion='reduce')
            seek(page,.1)
            static=image(page)
            seek(page,7)
            assert ImageChops.difference(static,image(page)).getbbox() is None, 'reduced motion changed'
            static.save(output/f'static-{theme}-{width}.png')
            assert page.locator('.static .exhibit').count()==6
            page.close()
            report.append({'theme':theme,'width':width,'texts':boxes,'reduced_motion':'pass','cycles':'pass'})
    return report


def previews(browser,output):
    page=browser.new_page(viewport={'width':600,'height':600})
    page.set_content(inline('dark',600))
    frames=[]
    for t in (.1,.65,1.2,2.3,4.5,6.8):
        seek(page,t)
        frames.append((t,image(page)))
    contact_sheet(frames,output/'storyboard.png')
    frames=[]
    for i in range(106):
        seek(page,i*.1)
        frames.append(image(page))
    frames[0].save(output/'legacy-intro.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
    page.close()
    dark=(ROOT/'profile/assets/legacy-dark.svg').as_uri()
    light=(ROOT/'profile/assets/legacy-light.svg').as_uri()
    html=f'''<!doctype html><meta charset="utf-8"><title>Old Mods / Legacy</title>
    <style>body{{max-width:1040px;margin:36px auto;background:#0d1117;padding:0 16px}}img{{display:block;width:100%}}
    @media(prefers-color-scheme:light){{body{{background:#fff}}}}</style>
    <picture><source media="(prefers-color-scheme:light)" srcset="{light}"><img src="{dark}" alt="Old Mods / Legacy"></picture>'''
    (output/'preview.html').write_text(html,encoding='utf-8')
    for theme in ('dark','light'):
        page=browser.new_page(viewport={'width':390,'height':900},color_scheme=theme)
        page.goto((output/'preview.html').as_uri())
        page.wait_for_function('document.images[0].complete && document.images[0].naturalWidth>0')
        assert f'legacy-{theme}.svg' in page.locator('img').evaluate('e=>e.currentSrc')
        page.wait_for_timeout(2500)
        page.locator('img').screenshot(path=str(output/f'image-{theme}-390.png'))
        page.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    output=parser.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(args=['--disable-lcd-text'])
        report=check(browser,output)
        previews(browser,output)
        browser.close()
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: both themes, mobile, text bounds, native motion, cycle phase, reduced motion and real IMG rendering')


if __name__=='__main__':
    main()
