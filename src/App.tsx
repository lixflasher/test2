import React, { useState, useEffect } from 'react';
import { Folder, FileCode, ChevronRight, ChevronDown, Download, Terminal, Play } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { motion, AnimatePresence } from 'framer-motion';

interface FileItem {
  path: string;
  name: string;
  type: 'file' | 'dir';
}

export default function App() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>('main.py');
  const [fileContent, setFileContent] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/files')
      .then(res => res.json())
      .then(data => {
        setFiles(data);
        setLoading(false);
        // Load main.py by default
        if (data.find((f: FileItem) => f.path === 'main.py')) {
            loadContent('main.py');
        }
      })
      .catch(err => console.error(err));
  }, []);

  const loadContent = async (path: string) => {
    setSelectedFile(path);
    try {
      const res = await fetch(`/api/file-content?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      setFileContent(data.content);
    } catch (err) {
      console.error(err);
    }
  };

  const getLanguage = (filename: string) => {
    if (filename.endsWith('.py')) return 'python';
    if (filename.endsWith('.json')) return 'json';
    if (filename.endsWith('.txt')) return 'text';
    return 'text';
  };

  // Group files by directory for display
  const fileTree = files.reduce((acc: any, file) => {
    const parts = file.path.split('/');
    if (parts.length === 1) {
        if (!acc['root']) acc['root'] = [];
        acc['root'].push(file);
    } else {
        const dir = parts[0];
        if (!acc[dir]) acc[dir] = [];
        acc[dir].push(file);
    }
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-[#1e1e1e] text-gray-300 font-sans flex flex-col">
      {/* Header */}
      <header className="bg-[#252526] border-b border-[#333] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-blue-400" />
          <h1 className="font-semibold text-white">Qidian Multi-Heroine Scraper</h1>
          <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded border border-blue-800">Python Project</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
           <div className="flex items-center gap-1 text-yellow-500">
             <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span>
             Generated Successfully
           </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-[#252526] border-r border-[#333] flex flex-col">
          <div className="p-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Explorer</div>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
                <div className="p-4 text-sm text-gray-500">Loading files...</div>
            ) : (
                <div className="px-2">
                    {/* Root Files */}
                    {fileTree['root']?.map((file: FileItem) => (
                        <FileRow 
                            key={file.path} 
                            file={file} 
                            selected={selectedFile === file.path}
                            onClick={() => loadContent(file.path)} 
                        />
                    ))}
                    
                    {/* Directories */}
                    {Object.keys(fileTree).filter(k => k !== 'root').map(dir => (
                        <div key={dir} className="mt-1">
                            <div className="flex items-center gap-1 px-2 py-1 text-sm text-gray-400 font-medium hover:text-white cursor-default">
                                <ChevronDown className="w-4 h-4" />
                                {dir}
                            </div>
                            <div className="pl-2">
                                {fileTree[dir].map((file: FileItem) => (
                                    <FileRow 
                                        key={file.path} 
                                        file={file} 
                                        selected={selectedFile === file.path}
                                        onClick={() => loadContent(file.path)} 
                                    />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col bg-[#1e1e1e] overflow-hidden">
            {/* Tabs */}
            <div className="flex bg-[#252526] border-b border-[#333]">
                {selectedFile && (
                    <div className="px-4 py-2 bg-[#1e1e1e] text-white text-sm border-t-2 border-blue-500 flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-blue-400" />
                        {selectedFile.split('/').pop()}
                    </div>
                )}
            </div>

            {/* Code Editor */}
            <div className="flex-1 overflow-auto relative">
                {selectedFile ? (
                    <SyntaxHighlighter
                        language={getLanguage(selectedFile)}
                        style={vscDarkPlus}
                        customStyle={{ margin: 0, padding: '1.5rem', minHeight: '100%', fontSize: '14px', lineHeight: '1.5' }}
                        showLineNumbers={true}
                    >
                        {fileContent}
                    </SyntaxHighlighter>
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                        Select a file to view content
                    </div>
                )}
            </div>
        </div>
      </div>

      {/* Instructions Panel */}
      <div className="h-48 bg-[#252526] border-t border-[#333] p-4 overflow-y-auto">
        <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
            <Play className="w-4 h-4 text-green-500" />
            How to Run Locally
        </h3>
        <div className="text-sm text-gray-400 space-y-2 font-mono">
            <p>1. Ensure you have Python 3.10+ and Chrome installed.</p>
            <p>2. Copy the files above to a local directory named <span className="text-orange-400">qidian_scraper</span>.</p>
            <p>3. Install dependencies:</p>
            <div className="bg-black/30 p-2 rounded text-gray-300 select-all">
                pip install -r requirements.txt
            </div>
            <p>4. Configure <span className="text-orange-400">config.json</span> with your LLM API key (Ollama or OpenAI).</p>
            <p>5. Run the scraper:</p>
            <div className="bg-black/30 p-2 rounded text-gray-300 select-all">
                python main.py
            </div>
        </div>
      </div>
    </div>
  );
}

function FileRow({ file, selected, onClick }: { file: FileItem, selected: boolean, onClick: () => void }) {
    if (file.type === 'dir') return null; // Handled by parent
    return (
        <div 
            onClick={onClick}
            className={`flex items-center gap-2 px-2 py-1 text-sm cursor-pointer rounded-sm mb-0.5 ${
                selected ? 'bg-[#37373d] text-white' : 'text-gray-400 hover:bg-[#2a2d2e] hover:text-gray-200'
            }`}
        >
            <FileCode className={`w-4 h-4 ${file.name.endsWith('.py') ? 'text-blue-400' : 'text-yellow-400'}`} />
            <span className="truncate">{file.name}</span>
        </div>
    );
}
