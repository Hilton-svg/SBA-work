// Minimal asar reader: extracts selected path prefixes from an Electron app.asar
import fs from 'node:fs'
import path from 'node:path'

const asarPath = process.argv[2]
const outDir = process.argv[3]
const wanted = process.argv.slice(4) // path prefixes inside the archive, e.g. /dsh/node_modules/@deepseek-ai/dsh-plugin-manager

const fd = fs.openSync(asarPath, 'r')

function read(fd, size, position) {
  const buf = Buffer.alloc(size)
  let readBytes = 0
  while (readBytes < size) {
    const n = fs.readSync(fd, buf, readBytes, size - readBytes, position + readBytes)
    if (n === 0) throw new Error('unexpected EOF')
    readBytes += n
  }
  return buf
}

const prefix = read(fd, 16, 0)
const headerSize = prefix.readUInt32LE(4)
const headerStrSize = prefix.readUInt32LE(12)
const headerBuf = read(fd, headerStrSize, 16)
const header = JSON.parse(headerBuf.toString('utf8'))
const baseOffset = 8 + headerSize
console.log('baseOffset', baseOffset)

const files = header.files
const links = header.links ?? []

function walk(node, currentPath, outPath) {
  for (const [name, entry] of Object.entries(node)) {
    const p = currentPath + '/' + name
    if (entry.files) {
      fs.mkdirSync(outPath + '/' + name, { recursive: true })
      walk(entry.files, p, outPath + '/' + name)
    } else if (entry.link !== undefined || entry.offset === undefined) {
      // symlink inside asar (no inline payload) — skip
    } else {
      const offset = Number(entry.offset)
      const buf = read(fd, Number(entry.size), baseOffset + offset)
      fs.mkdirSync(path.dirname(outPath + '/' + name), { recursive: true })
      fs.writeFileSync(outPath + '/' + name, buf)
    }
  }
}

function selectTree(node, prefixParts) {
  if (prefixParts.length === 0) return node
  const [head, ...rest] = prefixParts
  const child = node[head]
  if (!child) return null
  if (rest.length === 0) return child
  if (!child.files) return null
  const sub = selectTree(child.files, rest)
  if (!sub) return null
  return { __wrap: sub, __isFiles: true }
}

let total = 0
for (const want of wanted) {
  const parts = want.split('/').filter(Boolean)
  const node = selectTree(files, parts)
  if (!node) {
    console.log('MISS', want)
    continue
  }
  const target = path.join(outDir, ...parts)
  if (node.__isFiles) {
    fs.mkdirSync(target, { recursive: true })
    walk(node.__wrap, '/' + parts.join('/'), target)
  } else if (node.files) {
    fs.mkdirSync(target, { recursive: true })
    walk(node.files, '/' + parts.join('/'), target)
  } else {
    fs.mkdirSync(path.dirname(target), { recursive: true })
    fs.writeFileSync(target, read(fd, Number(node.size), baseOffset + Number(node.offset)))
  }
  console.log('OK', want, '->', target)
  total++
}

// also dump a directory listing of the archive roots for orientation
const roots = Object.keys(files)
console.log('archive roots:', roots.join(', '))
fs.writeFileSync(path.join(outDir, '__top-level.txt'), roots.join('\n'))
const dsh = files['dsh']
if (dsh?.files) {
  fs.writeFileSync(path.join(outDir, '__dsh-level.txt'), Object.keys(dsh.files).join('\n'))
  const nm = dsh.files['node_modules']
  if (nm?.files) {
    const scope = nm.files['@deepseek-ai']
    if (scope?.files) fs.writeFileSync(path.join(outDir, '__deepseek-ai-packages.txt'), Object.keys(scope.files).join('\n'))
  }
}
fs.closeSync(fd)
console.log('extracted', total)
