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

function dirNode(parts) {
  let node = header.files
  for (const p of parts) {
    node = node[p]
    if (!node) return null
  }
  return node.files ?? null
}

let count = 0
function walk(node, out) {
  fs.mkdirSync(out, { recursive: true })
  for (const [name, e] of Object.entries(node)) {
    if (e.files) walk(e.files, path.join(out, name))
    else if (e.offset !== undefined) {
      fs.writeFileSync(path.join(out, name), read(Number(e.size), base + Number(e.offset)))
      count++
    }
  }
}

const packages = process.argv.slice(2)
for (const pkg of packages) {
  const node = dirNode(['dsh', 'node_modules', '@deepseek-ai', pkg])
  if (!node) {
    console.log('MISS', pkg)
    continue
  }
  walk(node, path.join(outRoot, pkg))
  console.log('OK', pkg)
}
console.log('total files', count)
