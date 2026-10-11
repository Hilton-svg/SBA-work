// Validate the deploy script's generated patch text with the same YAML parser
// and `!!js` tag handling the DSH loader uses.
import { readFileSync } from 'node:fs'
import YAML from 'file:///E:/%E6%96%B0%E5%A2%9E%E8%B3%87%E6%96%99%E5%A4%BE/SBA-work/.dsh-scratch/asar2/__pkgs/yaml/dist/index.js'

const file = process.argv[2]
const text = readFileSync(file, 'utf8')

// Default tags: proves the document is well-formed YAML.
const plain = YAML.parse(text)
console.log('plain parse entries:', plain.length)
const row = plain.find((entry) => entry && entry.id === 'github-link')
console.log('github-link row:', JSON.stringify(row, null, 2))

// The loader's schema treats !!js as a tagged node; emulate it to prove the tag is accepted.
const tags = [{ tag: '!!js', resolve: (value) => ({ __jsExpr: String(value) }) }]
const withJs = YAML.parse(text, { customTags: tags })
const jsRow = withJs.find((entry) => entry && entry.id === 'github-link')
console.log('with !!js tag, entries:', withJs.length, 'repoRoot type:', typeof jsRow?.config?.repoRoot)
console.log('single-quoted windows path round-trip:', jsRow?.name)
console.log('OK')
