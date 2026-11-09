"""Small SVG helpers for a self-contained, script-free organization cover."""

import copy
from html import escape
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])
CYCLE = 9
START = 2.4


def text(x, y, value, size, color, **attrs):
    attrs = ' '.join(f'{key.rstrip("_").replace("_", "-")}="{escape(str(value), quote=True)}"' for key, value in attrs.items())
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {attrs}>{escape(value)}</text>'


def animation(attribute, values, duration, begin=0, *, kind=None, repeat=False, times=None, spline='.2 .8 .2 1'):
    if len(values) < 2 or duration <= 0:
        raise ValueError('Animation needs two values and a positive duration')
    times = times if times is not None else [i/(len(values)-1) for i in range(len(values))]
    if len(times) != len(values) or times[0] != 0 or times[-1] != 1 or any(a >= b for a,b in zip(times,times[1:])):
        raise ValueError('Keyframe times must increase from 0 to 1')
    attrs = dict(attributeName=attribute, values=';'.join(map(str,values)), keyTimes=';'.join(f'{t:g}' for t in times),
                 dur=f'{duration:g}s', begin=f'{begin:g}s', fill='freeze', calcMode='spline' if spline else 'linear')
    if spline:
        attrs['keySplines'] = ';'.join([spline]*(len(values)-1))
    if kind:
        attrs['type'] = kind
    if repeat:
        attrs['repeatCount'] = 'indefinite'
    tag = 'animateTransform' if kind else 'animate'
    return f'<{tag} ' + ' '.join(f'{k}="{escape(v,quote=True)}"' for k,v in attrs.items()) + '/>'


def arrive(body, offset='0 45', begin=.35, duration=1.6):
    return (f'<g class="arrive" opacity="0" transform="translate({offset})" data-rest-opacity="1" data-rest-transform="translate(0 0)">'
            + animation('opacity',[0,1],.6,begin)
            + animation('transform',[offset,'0 0'],duration,begin,kind='translate') + body + '</g>')


def loop(body, values, *, attribute='transform', kind='translate', times=None, rest=None):
    attrs = ''
    if rest is not None:
        attrs = f' {attribute}="{rest}" data-rest-{attribute}="{rest}"'
    return (f'<g class="detail-loop"{attrs}>'
            + animation(attribute,values,CYCLE,START,kind=kind,repeat=True,times=times,spline=None)
            + body + '</g>')


def static_layer(element):
    node = copy.deepcopy(element)
    for child in list(node.iter()):
        child.attrib.pop('id',None)
        for key,value in list(child.attrib.items()):
            if key.startswith('data-rest-'):
                child.set(key.removeprefix('data-rest-'),value)
                del child.attrib[key]
        for descendant in list(child):
            if descendant.tag in {NS+'animate',NS+'animateTransform',NS+'animateMotion',NS+'set'}:
                child.remove(descendant)
    node.set('class','static')
    return node


def serialize(markup):
    root = ET.fromstring(markup)
    scene = root.find(f'{NS}g[@id="scene"]')
    if scene is None:
        raise ValueError('Cover is missing its scene')
    root.insert(list(root).index(scene),static_layer(scene))
    scene.set('class','animated')
    return ET.tostring(root,encoding='unicode')+'\n'
