import fs from 'node:fs'
import path from 'node:path'

const asarPath = 'C:\\Users\\85292\\AppData\\Local\\Programs\\DeepSeek Harness\\resources\\app.asar'
const outRoot = 'E:\\新增資料夾\\SBA-work\\.dsh-scratch\\asar2'

const fd = fs.openSync(asarPath, 'r')
function read(size, position) {
  const buf = Buffer.alloc(size)
  let n = 0
  while (n < size) {
    const r = fs.readSync(fd, buf, n, size - n, position + n)
    if (!r) throw new Error('EOF')
    n += r
  }
  return buf
}
const prefix = read(16, 0)
const headerSize = prefix.readUInt32LE(4)
const headerStrSize = prefix.readUInt32LE(12)
const header = JSON.parse(read(headerStrSize, 16).toString('utf8'))
const base = 8 + headerSize

// Walk the asar tree by path segments. Directory entries hold `.files`;
// package directories are sometimes reached through a `link`-less wrapper.
function lookup(parts) {
  let node = header.files
  const trail = []
  for (const p of parts) {
    const child = node[p]
    if (!child) return { trail, node: null }
    trail.push(p)
    if (child.files) node = child.files
    else return { trail, node: child }
  }
  return { trail, node }
}

let count = 0
function walkFiles(node, out) {
  fs.mkdirSync(out, { recursive: true })
  for (const [name, e] of Object.entries(node)) {
    if (e.files) walkFiles(e.files, path.join(out, name))
    else if (e.offset !== undefined) {
      fs.writeFileSync(path.join(out, name), read(Number(e.size), base + Number(e.offset)))
      count++
    }
  }
}

const pkgScope = header.files.dsh.files.node_modules.files['@deepseek-ai']
console.log('scope children:', Object.keys(pkgScope.files).length)
fs.writeFileSync(path.join(outRoot, '__packages.txt'), Object.keys(pkgScope.files).join('\n'))

function pkgFiles(name) {
  const entry = pkgScope.files[name]
  if (!entry) return null
  if (entry.files) return entry.files
  if (entry.link !== undefined) {
    const target = entry.link.replace(/^\//, '').split('/')
    const { node } = lookup(target)
    return node?.files ?? null
  }
  return null
}

for (const pkg of process.argv.slice(2)) {
  const files = pkgFiles(pkg)
  if (!files) {
    console.log('MISS', pkg, JSON.stringify(pkgScope.files[pkg] ?? null).slice(0, 200))
    continue
  }
  walkFiles(files, path.join(outRoot, pkg))
  console.log('OK', pkg)
}
console.log('total files', count)
