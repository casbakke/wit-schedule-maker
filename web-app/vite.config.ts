import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import fs from 'node:fs/promises'
import { existsSync } from 'node:fs'

// https://vite.dev/config/
function localApiPlugin(): Plugin {
  const CALENDAR_BASE = path.resolve(process.cwd(), '../Calendar-Output')

  return {
    name: 'local-api-calendar-output',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        try {
          if (!req.url) return next()
          const url = new URL(req.url, 'http://localhost')

          // GET /api/runs -> list of subfolder names sorted by mtime desc
          if (url.pathname === '/api/runs') {
            if (!existsSync(CALENDAR_BASE)) {
              res.statusCode = 200
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify([]))
              return
            }

            const entries = await fs.readdir(CALENDAR_BASE, { withFileTypes: true })
            const folders = await Promise.all(
              entries
                .filter((e) => e.isDirectory())
                .map(async (e) => {
                  const p = path.join(CALENDAR_BASE, e.name)
                  const stat = await fs.stat(p)
                  return { name: e.name, mtime: stat.mtimeMs }
                })
            )
            folders.sort((a, b) => b.mtime - a.mtime)
            const names = folders.map((f) => f.name)
            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify(names))
            return
          }

          // GET /api/run/:name/files -> list of output*.csv sorted by numeric index
          if (url.pathname.startsWith('/api/run/') && url.pathname.endsWith('/files')) {
            const runName = decodeURIComponent(url.pathname.replace('/api/run/', '').replace('/files', ''))
            const runPath = path.join(CALENDAR_BASE, runName)
            const files = existsSync(runPath)
              ? (await fs.readdir(runPath)).filter((f) => /^output\d+\.csv$/i.test(f))
              : []
            files.sort((a, b) => {
              const na = parseInt(a.match(/(\d+)/)?.[1] || '0', 10)
              const nb = parseInt(b.match(/(\d+)/)?.[1] || '0', 10)
              return na - nb
            })
            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify(files))
            return
          }

          // GET /api/run/:name/file/:file -> raw CSV text
          if (url.pathname.startsWith('/api/run/') && url.pathname.includes('/file/')) {
            // Expected: /api/run/{runName}/file/{fileName}
            const parts = url.pathname.split('/') // ['', 'api', 'run', '{runName}', 'file', '{fileName}']
            const runName = decodeURIComponent(parts[3] || '')
            const fileName = decodeURIComponent(parts[5] || '')
            const filePath = path.join(CALENDAR_BASE, runName, fileName)
            if (!existsSync(filePath)) {
              res.statusCode = 404
              res.end('Not found')
              return
            }
            const text = await fs.readFile(filePath, 'utf8')
            res.statusCode = 200
            res.setHeader('Content-Type', 'text/csv; charset=utf-8')
            res.end(text)
            return
          }

          return next()
        } catch (err) {
          server.config.logger.error(`[local-api] ${String(err)}`)
          res.statusCode = 500
          res.end('Internal Server Error')
        }
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), localApiPlugin()],
  server: {
    fs: {
      // Allow reading the parent directory for Calendar-Output
      allow: [path.resolve(process.cwd(), '..')],
    },
  },
})
