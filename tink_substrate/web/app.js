const $ = id => document.getElementById(id);
const node = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
function link(url, text) {
  const n = node('a', text);
  try { const u = new URL(url); if (u.protocol === 'https:' && u.hostname === 'github.com') { n.href = u.href; n.target = '_blank'; n.rel = 'noopener noreferrer'; } } catch (_) {}
  return n;
}
function stamp(source) { return 'Checked ' + new Date(source.checked_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}); }
// A link the record has not reached yet is neutral; a failed read is a warning. Neither is shown as clean.
const linked = source => source.status !== 'not-linked';
function unavailable(source) { return linked(source) ? node('p', source.error || 'Unavailable', 'quiet warn') : node('p', source.reason, 'quiet'); }
const absent = source => linked(source) ? 'Unavailable' : 'Not linked';
let current;
function render(s) {
  current = s;
  const r = s.record, sources = s.sources;
  const g = sources.git.data, p = sources.github.data, w = sources.workflow.data;
  $('project').textContent = r.project;
  $('title').textContent = r.title;
  $('purpose').textContent = r.body.split('\n\n')[0].replace(/\n/g, ' ');
  $('next').textContent = r.next_action;
  $('owner').textContent = r.owner;
  $('origin').textContent = location.origin;
  $('record-path').textContent = 'Work record: ' + r.path;
  $('limits').textContent = s.limits;
  $('facts').replaceChildren();
  const fact = (label, value, detail, source, good, extra) => {
    const box = node('div', undefined, 'fact');
    box.append(node('p', label, 'fact-label'), node('strong', value, !linked(source) ? '' : good ? 'good' : 'warn'), node('p', detail));
    if (extra) box.append(extra);

    $('facts').append(box);
  };
  const selected = g?.worktrees.find(t => t.selected);
  const change = selected?.changes;
  fact('SELECTED CHECKOUT', !g || change?.status !== 'ok' ? 'Unavailable' : change.data.dirty ? 'Work in progress' : 'Clean', g ? g.branch : sources.git.error, sources.git, Boolean(g && change?.status === 'ok' && !change.data.dirty));
  fact('TINK-SDLC', w?.format === 'text' ? 'Text status' : w ? w.verification_status.replaceAll('-', ' ').replace(/^./, c => c.toUpperCase()) : absent(sources.workflow), w ? (w.next_action || 'No next action reported.') : sources.workflow.error || sources.workflow.reason, sources.workflow, w?.verification_status === 'current');
  fact('PULL REQUEST', p ? p.state === 'OPEN' ? p.isDraft ? 'Draft PR' : 'Open for review' : p.state === 'MERGED' ? 'Merged' : 'Closed' : absent(sources.github), p ? 'CI: ' + p.ci + ' · Approval: ' + (p.reviewDecision || 'not reported') : sources.github.error || sources.github.reason, sources.github, Boolean(p && p.ci === 'passed'), p ? link(p.url, '#' + p.number + ' · View pull request ↗') : null);
  $('worktrees').replaceChildren();
  $('branches').replaceChildren();
  $('tree-count').textContent = g ? g.worktrees.length + ' worktrees' : 'Unknown';
  if (!g) $('worktrees').append(unavailable(sources.git));
  for (const tree of g?.worktrees || []) {
    const box = node('div', undefined, 'tree'), head = node('div', undefined, 'tree-head');
    head.append(node('span', tree.branch));
    if (tree.selected) head.append(node('span', 'SELECTED', 'pill'));
    const c = tree.changes;
    head.append(node('span', c.status !== 'ok' ? 'UNKNOWN' : c.data.dirty ? c.data.count + ' CHANGED' : 'CLEAN', 'pill' + (c.status !== 'ok' || c.data.dirty ? ' warn' : '')));
    box.append(head, node('p', tree.path, 'path'));
    if (c.status !== 'ok') box.append(unavailable(c));
    else if (c.data.dirty) {
      const details = node('details'); details.append(node('summary', 'Changed paths'), node('pre', c.data.files.map(f => f.status + ' ' + f.path).join('\n') + (c.data.truncated ? '\n… More paths omitted' : ''))); box.append(details);
    }
    if (tree.locked || tree.prunable) box.append(node('p', tree.prunable ? 'Git marks this worktree as prunable; no cleanup was performed.' : 'Worktree locked: ' + tree.locked, 'quiet warn'));
    $('worktrees').append(box);
  }
  for (const b of g?.branches || []) $('branches').append(node('div', b.name + ' · ' + b.head.slice(0, 8) + (b.upstream ? ' · ' + b.upstream + ' ' + b.tracking : ' · no upstream'), 'branch'));
  $('evidence').replaceChildren();
  $('candidate').textContent = '';
  if (!w) $('evidence').append(unavailable(sources.workflow));
  if (w?.format === 'text') $('evidence').append(node('p', 'Installed SDLC status', 'fact-label'), node('pre', w.status_text));
  for (const item of w?.checklist || []) {
    const row = node('div', undefined, 'check'), text = node('div');
    text.append(node('p', item.description, 'check-title'), node('div', item.automatic ? 'Automated check' : 'Reported observation · not independent proof', 'check-meta'));
    if (item.mark?.evidence) { const details = node('details'); details.append(node('summary', 'Read observation'), node('pre', item.mark.evidence)); text.append(details); }
    if (item.needs_recheck) text.append(node('div', 'Attested before the latest change; recheck if affected.', 'check-meta warn'));
    row.append(node('span', item.status === 'passed' ? '✓' : '·', item.status === 'passed' ? 'good' : 'warn'), text, node('span', item.status, 'check-state'));
    $('evidence').append(row);
  }
  $('decisions').replaceChildren();
  if (w?.decisions.length) $('decisions').append(node('p', 'HUMAN DECISIONS RECORDED IN TINK-SDLC', 'fact-label'));
  for (const d of w?.decisions || []) {
    const row = node('div', undefined, 'check'), text = node('div');
    text.append(node('p', 'Stage ' + d.stage + ' ' + d.decision + (d.reviewer ? ' by ' + d.reviewer : ''), 'check-title'), node('div', [d.reason, d.source && 'Source: ' + d.source].filter(Boolean).join(' · '), 'check-meta'));
    row.append(node('span', d.decision === 'approved' ? '✓' : '·', d.decision === 'approved' ? 'good' : 'warn'), text, node('span', d.timestamp_ns ? new Date(d.timestamp_ns / 1e6).toLocaleDateString() : '', 'check-state'));
    $('decisions').append(row);
  }
  if (w) {
    if (w.format !== 'text' && !w.checklist?.length) $('evidence').append(node('p', 'No checklist evidence reported.', 'quiet warn'));
    const head = w.verification?.candidate?.head;
    $('candidate').textContent = head ? 'Last verified candidate: ' + head.slice(0,12) : '';
  }
  $('attention').replaceChildren();
  for (const item of s.attention) $('attention').append(node('li', item));
  $('attention-count').textContent = s.attention.length;
  if (!s.attention.length) $('attention').append(node('li', 'Nothing flagged.'));
  $('questions-panel').hidden = !(r.questions || []).length;
  $('questions').replaceChildren();
  for (const q of r.questions || []) $('questions').append(node('li', q));
  $('artifacts').replaceChildren();
  const light = w?.meta?.profile === 'light';
  for (const group of s.artifacts || []) {
    const section = node('section', undefined, 'artifact-stage');
    const heading = node('div', undefined, 'artifact-heading');
    heading.append(node('h3', group.title));
    section.append(heading);
    if (!group.documents.length) section.append(node('p', group.id === 'design' && light ? 'Included in the Plan brief.' : 'No saved artifacts yet.', 'artifact-note'));
    for (const doc of group.documents) {
      const details = node('details', undefined, 'artifact-document');
      details.append(node('summary', doc.label));
      details.append(node('p', doc.relative_path, 'path'));
      if (doc.status === 'ok') {
        const body = node('div', undefined, 'artifact-body');
        if (doc.label === 'Checklist') renderChecklist(body, doc.data.text);
        else if (doc.relative_path.endsWith('.json')) {
          let text = doc.data.text;
          try { text = JSON.stringify(JSON.parse(text), null, 2); } catch (_) {}
          body.append(node('pre', text));
        } else renderDocument(body, doc.data.text);
        details.append(body);
      } else details.append(node('p', doc.error || 'Unable to read file.', 'quiet warn'));
      section.append(details);
    }
    $('artifacts').append(section);
  }
  $('content').hidden = false;
  age();
}
function renderChecklist(container, text) {
  try {
    const value = JSON.parse(text);
    if (!Array.isArray(value.items)) throw new Error('Missing items');
    for (const item of value.items) {
      if (!item || typeof item.description !== 'string' || typeof item.verify !== 'string') throw new Error('Invalid item');
    }
    if (!value.items.length) container.append(node('p', 'No checklist items defined.'));
    for (const item of value.items) {
      const section = node('section', undefined, 'checklist-item');
      section.append(node('h4', item.description), node('p', item.verify));
      if (item.check && Array.isArray(item.check.argv)) {
        section.append(node('p', 'Automated check · ' + item.check.timeout_seconds + ' seconds', 'check-meta'));
        // JSON-quote arguments needing quoting; display only, never execute.
        section.append(node('pre', item.check.argv.map(a => /^[a-zA-Z0-9_./:-]+$/.test(a) ? a : JSON.stringify(a)).join(' ')));
      } else section.append(node('p', 'Attested observation · not automated proof', 'check-meta'));
      container.append(section);
    }
  } catch (_) {
    container.replaceChildren(node('p', 'Could not interpret this checklist. Original file:', 'warn'), node('pre', text));
  }
}
function renderDocument(container, text) {
  let code = null, paragraph = [];
  const flush = () => { if (paragraph.length) container.append(node('p', paragraph.join('\n'))); paragraph = []; };
  for (const line of text.split('\n')) {
    if (line.startsWith('```')) { flush(); if (code) { container.append(node('pre', code.join('\n'))); code = null; } else code = []; continue; }
    if (code) { code.push(line); continue; }
    if (!line.trim()) { flush(); continue; }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) { flush(); container.append(node('h4', heading[2])); }
    else if (/^\s*([-*]|\d+\.)\s/.test(line)) { flush(); container.append(node('p', line, 'document-item')); }
    else paragraph.push(line);
  }
  flush();
  if (code) container.append(node('pre', code.join('\n')));
}
function age() {
  if (!current) return;
  const seconds = Math.max(0, Math.floor((Date.now() - Date.parse(current.observed_at)) / 1000));
  $('age').textContent = seconds < 60 ? 'Checked ' + seconds + 's ago' : 'Snapshot ' + Math.floor(seconds/60) + 'm old · refresh before acting';
}
async function refresh(force = false) {
  $('refresh').disabled = true;
  $('notice').textContent = current ? 'Refreshing sources…' : 'Reading your selected project…';
  try {
    const response = await fetch('/api/snapshot' + (force ? '?refresh=1' : ''));
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not read sources.');
    render(data);
    $('notice').textContent = '';
  } catch (error) {
    $('notice').textContent = 'Refresh failed: ' + error.message + (current ? ' Showing the previous snapshot; its status may have changed.' : ' No current state is available.');
  } finally { $('refresh').disabled = false; }
}
$('refresh').addEventListener('click', () => refresh(true));
setInterval(age, 1000);
refresh();
