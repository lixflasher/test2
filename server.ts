import express from 'express';
import { createServer as createViteServer } from 'vite';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function startServer() {
  const app = express();
  const PORT = 3000;

  // API to list generated files
  app.get('/api/files', (req, res) => {
    const rootDir = path.join(__dirname, 'qidian_scraper');
    
    if (!fs.existsSync(rootDir)) {
      return res.status(404).json({ error: 'Project directory not found' });
    }

    const files: { path: string; name: string; type: 'file' | 'dir' }[] = [];

    function scanDir(dir: string, relativePath: string) {
      const items = fs.readdirSync(dir);
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        const itemRelativePath = path.join(relativePath, item);
        
        if (stat.isDirectory()) {
            if (item !== '__pycache__' && item !== '.git') {
                 files.push({ path: itemRelativePath, name: item, type: 'dir' });
                 scanDir(fullPath, itemRelativePath);
            }
        } else {
          files.push({ path: itemRelativePath, name: item, type: 'file' });
        }
      }
    }

    scanDir(rootDir, '');
    res.json(files);
  });

  // API to get file content
  app.get('/api/file-content', (req, res) => {
    const filePath = req.query.path as string;
    if (!filePath) return res.status(400).json({ error: 'Path required' });

    const fullPath = path.join(__dirname, 'qidian_scraper', filePath);
    
    // Security check: prevent directory traversal
    if (!fullPath.startsWith(path.join(__dirname, 'qidian_scraper'))) {
        return res.status(403).json({ error: 'Access denied' });
    }

    if (!fs.existsSync(fullPath)) return res.status(404).json({ error: 'File not found' });

    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      res.json({ content });
    } catch (e) {
      res.status(500).json({ error: 'Failed to read file' });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
