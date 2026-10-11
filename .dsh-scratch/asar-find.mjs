import fs from 'node:fs'
import path from 'node:path'

const asarPath = 'C:\\Users\\85292\\AppData\\Local\\Programs\\DeepSeek Harness\\resources\\app.asar'
const outRoot = 'E:\\新增資料夾\\SBA-work\\.dsh-scratch\\asar2'
const want = process.argv[2]

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

// Find every directory named `want` anywhere in the archive.
const hits = []
function search(node, trail) {
  for (const [name, entry] of Object.entries(node)) {
    if (!entry.files) continue
    const next = [...trail, name]
    if (name === want) hits.push({ trail: next, files: entry.files })
    search(entry.files, next)
  }
}
search(header.files, [])

console.log('hits for', want, ':', hits.map((hit) => '/' + hit.trail.join('/')).join('\n  '))

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

const target = hits[0]
if (target !== undefined) {
  const out = path.join(outRoot, '__pkgs', want)
  walk(target.files, out)
  console.log('extracted to', out, count, 'files')
}
