const SVG_NS = 'http://www.w3.org/2000/svg';
const CENTER = 50;
const RADIUS = 48.6;

/**
 * 球外的双圈与四道细刻度：像制版的规矩线，安静地界住球面。
 */
export function buildDial(host) {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 100 100');
  svg.setAttribute('aria-hidden', 'true');

  svg.append(
    circle(RADIUS, { 'stroke-width': 0.2, opacity: 0.32 }),
    circle(RADIUS + 2.6, {
      'stroke-width': 0.9,
      'stroke-dasharray': '0.3 3.4',
      'stroke-linecap': 'round',
      opacity: 0.3,
    }),
  );

  for (let i = 0; i < 4; i += 1) {
    const angle = (i / 4) * Math.PI * 2;
    const line = document.createElementNS(SVG_NS, 'line');
    const outer = RADIUS + 2.9;
    const inner = RADIUS + 1.3;
    line.setAttribute('x1', point(outer, angle).x.toFixed(2));
    line.setAttribute('y1', point(outer, angle).y.toFixed(2));
    line.setAttribute('x2', point(inner, angle).x.toFixed(2));
    line.setAttribute('y2', point(inner, angle).y.toFixed(2));
    line.setAttribute('stroke', 'currentColor');
    line.setAttribute('stroke-width', '0.34');
    line.setAttribute('opacity', '0.5');
    svg.append(line);
  }

  host.replaceChildren(svg);
}

function circle(radius, attrs) {
  const node = document.createElementNS(SVG_NS, 'circle');
  node.setAttribute('cx', CENTER);
  node.setAttribute('cy', CENTER);
  node.setAttribute('r', String(radius));
  node.setAttribute('fill', 'none');
  node.setAttribute('stroke', 'currentColor');
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
  return node;
}

function point(radius, angle) {
  return {
    x: CENTER + radius * Math.sin(angle),
    y: CENTER - radius * Math.cos(angle),
  };
}
