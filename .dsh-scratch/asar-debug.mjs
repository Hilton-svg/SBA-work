import fs from 'node:fs'
const asarPath = process.argv[2]
const fd = fs.openSync(asarPath, 'r')
function read(size, position) {
  const buf = Buffer.alloc(size)
  let n = 0
  while (n < size) {
    const r = fs.readSync(fd, buf, n, size - n, position + n)
    if (r === 0) throw new Error('EOF')
    n += r
  }
  return buf
}
const prefix = read(16, 0)
const headerSize = prefix.readUInt32LE(4)
const headerStrSize = prefix.readUInt32LE(12)
const header = JSON.parse(read(headerStrSize, 16).toString('utf8'))
const files = header.files
const node = files.dsh.files.node_modules.files['@deepseek-ai'].files['dsh-plugin-manager']
console.log('keys:', Object.keys(node).slice(0, 20))
console.log('sample:', JSON.stringify(node[Object.keys(node)[0]]))
console.log('has files?', !!node.files)
console.log('typeof:', typeof node)
