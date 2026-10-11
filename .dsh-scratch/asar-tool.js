// Local scratch helper: read/extract files from an Electron app.asar archive.
const fs = require('fs');
const path = require('path');

const archive = process.argv[2];
const mode = process.argv[3];

function readHeader(p) {
  const fd = fs.openSync(p, 'r');
  const b = Buffer.alloc(16);
  fs.readSync(fd, b, 0, 16, 0);
  const jsonSize = b.readUInt32LE(12);
  const jb = Buffer.alloc(jsonSize);
  fs.readSync(fd, jb, 0, jsonSize, 16);
  fs.closeSync(fd);
  return { header: JSON.parse(jb.toString('utf8')), base: 16 + jsonSize };
}

const { header, base } = readHeader(archive);
const dataOffset = base;

function getNode(rel) {
  const parts = rel.split('/').filter(Boolean);
  let node = header.files;
  let entry;
  for (const part of parts) {
    if (!node || !node[part]) return undefined;
    entry = node[part];
    node = entry.files;
  }
  return entry;
}

function walk(node, prefix, out) {
  for (const [name, entry] of Object.entries(node)) {
    const full = prefix ? prefix + '/' + name : name;
    if (entry.files) walk(entry.files, full, out);
    else out.push({ path: full, size: entry.size, offset: entry.offset });
  }
}

if (mode === 'list') {
  const prefix = process.argv[4] || '';
  const node = getNode(prefix);
  if (!node) { console.error('not found: ' + prefix); process.exit(1); }
  console.log(Object.keys(node).join('\n'));
} else if (mode === 'find') {
  const re = new RegExp(process.argv[4]);
  const out = [];
  walk(header.files, '', out);
  for (const f of out) if (re.test(f.path)) console.log(f.path + '\t' + f.size);
} else if (mode === 'read') {
  const rel = process.argv[4];
  const node = getNode(rel);
  if (!node) { console.error('not found: ' + rel); process.exit(1); }
  const fd = fs.openSync(archive, 'r');
  const buf = Buffer.alloc(node.size);
  fs.readSync(fd, buf, 0, node.size, dataOffset + Number(node.offset));
  fs.closeSync(fd);
  process.stdout.write(buf);
} else if (mode === 'extract') {
  const prefix = process.argv[4];
  const dest = process.argv[5];
  const node = getNode(prefix);
  if (!node) { console.error('not found: ' + prefix); process.exit(1); }
  const fd = fs.openSync(archive, 'r');
  const out = [];
  walk(node, prefix, out);
  for (const f of out) {
    const target = path.join(dest, f.path);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    const buf = Buffer.alloc(f.size);
    if (f.size) fs.readSync(fd, buf, 0, f.size, dataOffset + Number(f.offset));
    fs.writeFileSync(target, buf);
  }
  fs.closeSync(fd);
  console.log('extracted ' + out.length + ' files to ' + dest);
} else {
  console.error('usage: node asar-tool.js <archive> list|find|read|extract ...');
  process.exit(1);
}
