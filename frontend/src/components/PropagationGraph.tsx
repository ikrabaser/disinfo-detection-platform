import CytoscapeComponent from "react-cytoscapejs";
import type { Core, ElementDefinition, Stylesheet } from "cytoscape";

import type { PropagationGraphData } from "../types";

const MOCK_GRAPH: PropagationGraphData = {
  nodes: [
    { id: "source-01", type: "post" },
    { id: "post-02", type: "post" },
    { id: "post-03", type: "post" },
    { id: "post-04", type: "post" },
    { id: "post-05", type: "post" },
    { id: "post-06", type: "post" },
    { id: "post-07", type: "post" },
    { id: "post-08", type: "post" },
    { id: "post-09", type: "post" },
    { id: "post-10", type: "post" },
    { id: "post-11", type: "post" },
    { id: "post-12", type: "post" },
    { id: "post-13", type: "post" },
    { id: "post-14", type: "post" },
    { id: "post-15", type: "post" },
  ],
  edges: [
    { source: "source-01", target: "post-02" },
    { source: "source-01", target: "post-03" },
    { source: "source-01", target: "post-04" },
    { source: "source-01", target: "post-05" },
    { source: "post-02", target: "post-06" },
    { source: "post-02", target: "post-07" },
    { source: "post-03", target: "post-08" },
    { source: "post-03", target: "post-09" },
    { source: "post-04", target: "post-10" },
    { source: "post-04", target: "post-11" },
    { source: "post-06", target: "post-12" },
    { source: "post-08", target: "post-13" },
    { source: "post-10", target: "post-14" },
    { source: "post-11", target: "post-15" },
    { source: "post-07", target: "post-13" },
  ],
};

function toElements(data: PropagationGraphData): ElementDefinition[] {
  const nodeElements: ElementDefinition[] = data.nodes.map((node, index) => ({
    data: {
      id: node.id,
      label: index === 0 ? "Kaynak" : "",
      root: index === 0 ? "true" : "false",
    },
  }));

  const edgeElements: ElementDefinition[] = data.edges.map((edge, index) => ({
    data: {
      id: `edge-${index}`,
      source: edge.source,
      target: edge.target,
    },
  }));

  return [...nodeElements, ...edgeElements];
}

const layout = {
  name: "cose",
  animate: false,
  fit: true,
  padding: 28,
  nodeRepulsion: 9000,
  idealEdgeLength: 75,
};

const stylesheet: Stylesheet[] = [
  {
    selector: "node",
    style: {
      "background-color": "#2563eb",
      "border-color": "#ffffff",
      "border-width": 2,
      width: 18,
      height: 18,
      label: "data(label)",
      color: "#334155",
      "font-size": 10,
      "text-valign": "bottom",
      "text-margin-y": 6,
    },
  },
  {
    selector: 'node[root = "true"]',
    style: {
      "background-color": "#dc2626",
      width: 30,
      height: 30,
    },
  },
  {
    selector: "edge",
    style: {
      width: 1.25,
      "line-color": "#cbd5e1",
      "target-arrow-color": "#94a3b8",
      "target-arrow-shape": "triangle",
      "arrow-scale": 0.7,
      "curve-style": "bezier",
    },
  },
];

interface Props {
  data?: PropagationGraphData;
}

export default function PropagationGraph({ data = MOCK_GRAPH }: Props) {
  const elements = toElements(data);

  return (
    <div className="h-full rounded-lg border border-slate-200 bg-white">
      <div className="flex items-start justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            Yayılım Ağı
          </h3>

          <p className="mt-1 text-xs text-slate-500">
            İçeriğin paylaşım zinciri ve ilişkili hesap kümeleri
          </p>
        </div>

        <div className="text-right">
          <p className="text-xs font-medium text-slate-700">
            {data.nodes.length} düğüm
          </p>
          <p className="mt-0.5 text-xs text-slate-400">
            {data.edges.length} bağlantı
          </p>
        </div>
      </div>

      <div className="px-3 py-2">
        <CytoscapeComponent
          elements={elements}
          style={{
            width: "100%",
            height: "360px",
            background: "#ffffff",
          }}
          layout={layout}
          stylesheet={stylesheet}
          cy={(cy: Core) => {
            cy.on("tap", "node", (event) => {
              console.log("Selected node:", event.target.id());
            });
          }}
        />
      </div>

      <div className="flex items-center gap-5 border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
          Kaynak içerik
        </span>

        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
          Yayılım düğümü
        </span>
      </div>
    </div>
  );
}
