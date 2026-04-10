import React, { useState, useCallback } from "react";
import { motion } from "motion/react";
import { Database, Bot, Layout, Play, Share, Settings2, Plus, ArrowRight, FileText, Github, MessageSquare, Sparkles, CheckCircle2 } from "lucide-react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  Handle,
  Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Custom Node Components
const DataSourceNode = ({ data }: { data: any }) => (
  <div className="p-4 rounded-2xl border-2 border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 shadow-sm min-w-[150px]">
    <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-neutral-500" />
    <div className="flex items-center gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${data.colorClass}`}>
        {data.icon}
      </div>
      <div>
        <p className="text-sm font-bold text-neutral-900 dark:text-white">{data.label}</p>
        <p className="text-xs text-neutral-500">{data.sublabel}</p>
      </div>
    </div>
  </div>
);

const AINode = ({ data }: { data: any }) => (
  <div className="p-5 rounded-2xl border-2 border-neutral-500 bg-white dark:bg-neutral-900 shadow-md min-w-[250px]">
    <Handle type="target" position={Position.Top} className="w-3 h-3 bg-neutral-500" />
    <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-neutral-500" />
    <div className="flex items-center gap-4 mb-3">
      <div className="w-12 h-12 rounded-xl bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center">
        <Bot className="w-6 h-6" />
      </div>
      <div>
        <p className="text-base font-bold text-neutral-900 dark:text-white">{data.label}</p>
        <p className="text-sm text-neutral-500">AI Function</p>
      </div>
    </div>
  </div>
);

const OutputNode = ({ data }: { data: any }) => (
  <div className="p-4 rounded-2xl border-2 border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 shadow-sm min-w-[200px]">
    <Handle type="target" position={Position.Top} className="w-3 h-3 bg-neutral-500" />
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center">
        <MessageSquare className="w-5 h-5" />
      </div>
      <div>
        <p className="text-sm font-bold text-neutral-900 dark:text-white">{data.label}</p>
        <p className="text-xs text-neutral-500">Interactive UI</p>
      </div>
    </div>
  </div>
);

const nodeTypes = {
  dataSource: DataSourceNode,
  aiFunction: AINode,
  output: OutputNode,
};

const initialNodes: Node[] = [
  {
    id: 'data-1',
    type: 'dataSource',
    position: { x: 100, y: 50 },
    data: { 
      label: 'Resume', 
      sublabel: 'PDF Document',
      icon: <FileText className="w-5 h-5" />,
      colorClass: 'bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400'
    },
  },
  {
    id: 'data-2',
    type: 'dataSource',
    position: { x: 350, y: 50 },
    data: { 
      label: 'GitHub', 
      sublabel: 'API Source',
      icon: <Github className="w-5 h-5" />,
      colorClass: 'bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400'
    },
  },
  {
    id: 'ai-node',
    type: 'aiFunction',
    position: { x: 200, y: 200 },
    data: { label: 'Career Gap Analyzer' },
  },
  {
    id: 'output-node',
    type: 'output',
    position: { x: 225, y: 350 },
    data: { label: 'Recruiter Chatbot' },
  },
];

const initialEdges: Edge[] = [
  { id: 'e1', source: 'data-1', target: 'ai-node', animated: true },
  { id: 'e2', source: 'data-2', target: 'ai-node', animated: true },
  { id: 'e3', source: 'ai-node', target: 'output-node', animated: true },
];

export default function BuilderPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<string | null>("ai-node");
  const [isPublishing, setIsPublishing] = useState(false);
  const [published, setPublished] = useState(false);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const handlePublish = () => {
    setIsPublishing(true);
    setTimeout(() => {
      setIsPublishing(false);
      setPublished(true);
    }, 2000);
  };

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id);
  };

  const onPaneClick = () => {
    setSelectedNode(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="h-[calc(100vh-8rem)] flex flex-col"
    >
      <header className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">AI App Studio</h1>
          <p className="text-neutral-600 dark:text-neutral-400">Build custom AI workflows by connecting data sources to AI functions.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-xl font-medium hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors flex items-center gap-2">
            <Play className="w-4 h-4" /> Test Run
          </button>
          <button 
            onClick={handlePublish}
            disabled={isPublishing || published}
            className={`px-5 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
              published 
                ? "bg-neutral-500 text-white" 
                : "bg-neutral-600 hover:bg-neutral-700 text-white"
            }`}
          >
            {isPublishing ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Publishing...</>
            ) : published ? (
              <><CheckCircle2 className="w-4 h-4" /> Published</>
            ) : (
              <><Share className="w-4 h-4" /> Publish App</>
            )}
          </button>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        
        {/* Left Sidebar: Blocks Palette */}
        <div className="lg:col-span-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-5 flex flex-col overflow-y-auto custom-scrollbar shadow-sm dark:shadow-none">
          <h3 className="font-semibold text-neutral-900 dark:text-white mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-neutral-500" /> Add Blocks
          </h3>
          
          <div className="space-y-6">
            {/* Data Sources */}
            <div>
              <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider mb-3">Data Sources</h4>
              <div className="space-y-2">
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center shrink-0"><FileText className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Resume PDF</span>
                </div>
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center shrink-0"><Github className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">GitHub Repo</span>
                </div>
              </div>
            </div>

            {/* AI Functions */}
            <div>
              <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider mb-3">AI Functions</h4>
              <div className="space-y-2">
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center shrink-0"><Bot className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Gap Analyzer</span>
                </div>
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center shrink-0"><Sparkles className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Custom Prompt</span>
                </div>
              </div>
            </div>

            {/* UI Components */}
            <div>
              <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider mb-3">Outputs & UI</h4>
              <div className="space-y-2">
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center shrink-0"><MessageSquare className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Chat Interface</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Middle: Canvas (React Flow) */}
        <div className="lg:col-span-6 bg-neutral-100 dark:bg-neutral-950/50 border border-neutral-200 dark:border-neutral-800 rounded-3xl relative overflow-hidden shadow-inner">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            fitView
            className="bg-neutral-100 dark:bg-neutral-950/50"
          >
            <Background color="#888" gap={24} />
            <Controls className="bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 fill-neutral-700 dark:fill-neutral-300" />
          </ReactFlow>
        </div>

        {/* Right Sidebar: Configuration */}
        <div className="lg:col-span-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-5 flex flex-col overflow-y-auto custom-scrollbar shadow-sm dark:shadow-none">
          <h3 className="font-semibold text-neutral-900 dark:text-white mb-6 flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-neutral-500" /> Configuration
          </h3>

          {!selectedNode && (
            <div className="text-center text-neutral-500 dark:text-neutral-400 mt-10">
              Select a node to configure it.
            </div>
          )}

          {selectedNode === "ai-node" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Block Name</label>
                <input type="text" defaultValue="Career Gap Analyzer" className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">System Prompt (Plain English)</label>
                <textarea 
                  rows={6} 
                  defaultValue="Compare my resume and GitHub repos against entry-level React developer roles. Highlight missing skills. Always cite which project or resume section you are referencing."
                  className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50 resize-none" 
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Model Selection</label>
                <select className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50">
                  <option>Gemini 1.5 Flash (Fast)</option>
                  <option>Gemini 1.5 Pro (Advanced)</option>
                </select>
              </div>
            </motion.div>
          )}

          {selectedNode === "data-1" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Source Name</label>
                <input type="text" defaultValue="Resume" className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50" />
              </div>
              <div className="p-4 border border-neutral-200 dark:border-neutral-800 rounded-xl bg-neutral-50 dark:bg-neutral-950 flex items-center justify-between">
                <span className="text-sm font-medium text-neutral-900 dark:text-white">johndoe_resume.pdf</span>
                <button className="text-xs text-neutral-500 font-medium">Replace</button>
              </div>
            </motion.div>
          )}

          {selectedNode === "data-2" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Connection</label>
                <div className="p-3 border border-neutral-200 dark:border-neutral-900/50 bg-neutral-50 dark:bg-neutral-500/10 rounded-xl flex items-center gap-2 text-neutral-700 dark:text-neutral-400 text-sm font-medium">
                  <CheckCircle2 className="w-4 h-4" /> Authenticated as @johndoe
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Included Repositories</label>
                <select className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50">
                  <option>All Public Repos</option>
                  <option>Selected Repos Only...</option>
                </select>
              </div>
            </motion.div>
          )}

          {selectedNode === "output-node" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Interface Type</label>
                <select className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50">
                  <option>Conversational Chatbot</option>
                  <option>Static Dashboard</option>
                  <option>API Endpoint</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Welcome Message</label>
                <textarea 
                  rows={3} 
                  defaultValue="Hi! I'm John's AI assistant. Ask me anything about his experience, projects, or skills."
                  className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50 resize-none" 
                />
              </div>
            </motion.div>
          )}

        </div>
      </div>
    </motion.div>
  );
}
