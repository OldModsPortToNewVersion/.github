"""Validate both themes, local references, timing and accessible static layers."""

import re
import base64
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET

from build_cover import HEIGHT, WIDTH, build
from relics import RELICS, ASSET_ROOT
from svg import CYCLE, NS, START, animation


class CoverTests(unittest.TestCase):
    def test_cover_is_self_contained_and_ids_are_unique(self):
        for theme in ('dark','light'):
            markup=build(theme)
            root=ET.fromstring(markup)
            self.assertEqual(root.get('viewBox'),f'0 0 {WIDTH} {HEIGHT}')
            ids=[node.get('id') for node in root.iter() if node.get('id')]
            self.assertEqual(len(ids),len(set(ids)))
            for node in root.iter():
                self.assertNotIn(node.tag,(NS+'script',NS+'foreignObject'))
                if 'href' in node.attrib:
                    self.assertTrue(node.get('href').startswith(('#','data:image/png;base64,')))
                    if node.get('href').startswith('#'):
                        self.assertIn(node.get('href')[1:],ids)
                for value in node.attrib.values():
                    for reference in re.findall(r'url\(#([^)]*)\)',value):
                        self.assertIn(reference,ids)
            self.assertIn('prefers-reduced-motion:reduce',markup)
            self.assertNotIn('@keyframes',markup)

    def test_every_mod_has_a_label_and_its_own_illustration(self):
        root=ET.fromstring(build('dark'))
        for name,label,_,_,_ in RELICS:
            scene=root.find(f'.//{NS}g[@id="relic-{name}"]')
            self.assertIsNotNone(scene)
            self.assertIn(label,''.join(scene.itertext()))
            images=scene.findall('.//'+NS+'use')
            self.assertTrue(images)
            self.assertTrue(all(image.get('href').startswith('#image-') for image in images))

    def test_embedded_images_match_the_downloaded_source_pixels(self):
        root=ET.fromstring(build('dark'))
        manifest=json.loads((ASSET_ROOT/'sources.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest),7)
        for name,spec in manifest.items():
            symbol=root.find(f'.//{NS}symbol[@id="image-{name}"]')
            image=symbol.find(NS+'image')
            png=base64.b64decode(image.get('href').split(',',1)[1],validate=True)
            self.assertEqual(png,(ASSET_ROOT/f'{name}.png').read_bytes())
            self.assertEqual(hashlib.sha256(png).hexdigest(),spec['png_sha256'])
        self.assertIn('original Applied Energistics',manifest['me-drive']['description'])

    def test_reduced_motion_has_finished_visible_artwork(self):
        root=ET.fromstring(build('dark'))
        static=root.find(f'{NS}g[@class="static"]')
        self.assertIsNotNone(static)
        self.assertFalse(static.findall('.//'+NS+'animate'))
        self.assertFalse(static.findall('.//'+NS+'animateTransform'))
        arrivals=[n for n in static.iter() if n.get('class')=='arrive']
        self.assertGreater(len(arrivals),20)
        self.assertTrue(all(n.get('opacity')=='1' and n.get('transform')=='translate(0 0)' for n in arrivals))

    def test_all_loops_share_one_phase_and_period(self):
        root=ET.fromstring(build('dark'))
        effects=[node for node in root.iter() if node.tag in (NS+'animate',NS+'animateTransform')]
        self.assertGreater(len(effects),40)
        for effect in effects:
            times=list(map(float,effect.get('keyTimes').split(';')))
            self.assertEqual(times,sorted(set(times)))
            self.assertEqual((times[0],times[-1]),(0,1))
            self.assertEqual(len(times),len(effect.get('values').split(';')))
            if effect.get('repeatCount')=='indefinite':
                self.assertEqual(effect.get('begin'),f'{START:g}s')
                self.assertEqual(effect.get('dur'),f'{CYCLE:g}s')
            else:
                self.assertLessEqual(float(effect.get('begin')[:-1])+float(effect.get('dur')[:-1]),START)

    def test_generation_is_deterministic(self):
        for theme in ('dark','light'):
            self.assertEqual(build(theme),build(theme))

    def test_malformed_timing_is_rejected(self):
        for values,times,duration in (([0],None,1),([0,1],[0,.5],1),([0,1],[0,1],0),([0,1,2],[0,0,1],1)):
            with self.assertRaises(ValueError):
                animation('opacity',values,duration,times=times)


if __name__=='__main__':
    unittest.main()
