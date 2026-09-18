const form = document.querySelector('#config-form');
const canvas = document.querySelector('#canvas');
const error = document.querySelector('#error');
const total = document.querySelector('#seat-total');
const planSize = document.querySelector('#plan-size');
let plan;

function payload() {
  const data = Object.fromEntries(new FormData(form));
  for (const key of ['seats_per_table', 'num_tables_x', 'num_tables_y', 'gap_seats_x', 'gap_seats_y', 'seat_radius', 'margin']) data[key] = Number(data[key]);
  for (const key of ['gap_tables_x', 'gap_tables_y']) {
    data[key] = data[key].split(',').map(value => Number(value.trim())).filter(value => Number.isFinite(value));
  }
  return data;
}

function seatCount(data) { return data.seats_per_table * data.num_tables_x * data.num_tables_y; }

function updateNumberingOptions() {
  const primary = form.elements.primary_numbering;
  const secondary = form.elements.secondary_numbering;
  const primaryIsHorizontal = ['left-to-right', 'right-to-left'].includes(primary.value);
  for (const option of secondary.options) {
    const secondaryIsHorizontal = ['left-to-right', 'right-to-left'].includes(option.value);
    option.disabled = primaryIsHorizontal === secondaryIsHorizontal;
  }
  if (secondary.selectedOptions[0].disabled) secondary.value = primaryIsHorizontal ? 'top-to-bottom' : 'left-to-right';
}

function render(data) {
  const zone = data.zones[0];
  const { width, height } = data.size;
  planSize.textContent = `${Math.round(width)} × ${Math.round(height)} units`;
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip';
  document.body.append(tooltip);

  const benches = zone.areas.map((area, index) => {
    const { x, y } = area.position;
    const { width, height } = area.rectangle;
    return `<g data-table="${index + 1}"><rect class="bench" x="${x}" y="${y}" width="${width}" height="${height}" rx="3"/><text class="table-number" x="${x + width / 2}" y="${y + height / 2}">${index + 1}</text></g>`;
  }).join('');
  const seats = zone.rows.flatMap(row => row.seats.map(seat => `<circle class="seat" data-guid="${seat.seat_guid}" cx="${row.position.x + seat.position.x}" cy="${row.position.y + seat.position.y}" r="${seat.radius}"/>`)).join('');
  canvas.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img"><g id="viewport">${benches}${seats}</g></svg>`;

  const svg = canvas.querySelector('svg');
  const viewport = svg.querySelector('#viewport');
  let zoom = 1, panX = 0, panY = 0, drag;
  const update = () => viewport.setAttribute('transform', `translate(${panX} ${panY}) scale(${zoom})`);
  svg.addEventListener('wheel', event => { event.preventDefault(); zoom = Math.min(4, Math.max(.35, zoom * (event.deltaY < 0 ? 1.12 : .89))); update(); }, { passive:false });
  svg.addEventListener('pointerdown', event => { drag = { x:event.clientX, y:event.clientY }; svg.setPointerCapture(event.pointerId); });
  svg.addEventListener('pointermove', event => {
    if (drag) { panX += (event.clientX - drag.x) / svg.clientWidth * width / zoom; panY += (event.clientY - drag.y) / svg.clientHeight * height / zoom; drag = { x:event.clientX, y:event.clientY }; update(); }
    const seat = event.target.closest('.seat');
    if (seat) { tooltip.textContent = seat.dataset.guid; tooltip.style.left = `${event.clientX}px`; tooltip.style.top = `${event.clientY}px`; tooltip.classList.add('visible'); } else tooltip.classList.remove('visible');
  });
  svg.addEventListener('pointerup', () => { drag = undefined; });
  svg.addEventListener('pointerleave', () => tooltip.classList.remove('visible'));
}

async function generate() {
  error.textContent = '';
  const data = payload();
  total.textContent = `${seatCount(data).toLocaleString()} seats`;
  const response = await fetch('/api/seating', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
  if (!response.ok) throw new Error((await response.json()).detail || 'The plan could not be generated.');
  plan = await response.json();
  render(plan);
}

form.addEventListener('submit', async event => { event.preventDefault(); try { await generate(); } catch (err) { error.textContent = err.message; } });
form.elements.primary_numbering.addEventListener('change', updateNumberingOptions);
document.querySelector('#download').addEventListener('click', async () => {
  try { if (!plan) await generate(); const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([JSON.stringify(plan, null, 2)], { type:'application/json' })); link.download = 'beer-benches-seating.json'; link.click(); URL.revokeObjectURL(link.href); } catch (err) { error.textContent = err.message; }
});
updateNumberingOptions();
generate().catch(err => { error.textContent = err.message; });
