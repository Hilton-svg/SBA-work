// Read-only check against the real workspace repository through the plugin's tools.
import { apply } from 'file:///E:/%E6%96%B0%E5%A2%9E%E8%B3%87%E6%96%99%E5%A4%BE/SBA-work/dsh-github-link/index.js'
import { pathToFileURL } from 'node:url'

console.log('plugin url ok:', pathToFileURL('E:/新增資料夾/SBA-work/dsh-github-link/index.js').href)

const tools = new Map()
const ctx = {
  tools: { register: (d) => tools.set(d.name, d) },
  provide: (name, service) => console.log(`[provide] ${name} (enabled=${service.describe().enabled})`),
  on: (event) => console.log(`[on] ${event}`),
  logger: () => ({ info: (m) => console.log(`[info] ${m}`), warn: (m) => console.log(`[warn] ${m}`) }),
}

apply(ctx, { repoRoot: 'E:\\新增資料夾\\SBA-work', timeoutMs: 60000, credentialsFile: 'E:\\新增資料夾\\SBA-work\\.dsh-scratch\\creds.json' })

const show = (label, text) => {
  console.log(`\n===== ${label} =====`)
  console.log(text)
}

const github = tools.get('github')
show('snapshot', await github.execute({ action: 'snapshot' }, {}))
show('log (3)', await github.execute({ action: 'log', limit: 3 }, {}))
show('sync dryRun', await github.execute({ action: 'sync', dryRun: true }, {}))
const auth = tools.get('github_auth')
show('auth status', await auth.execute({ action: 'status' }, {}))
