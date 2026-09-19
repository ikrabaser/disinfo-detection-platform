import CytoscapeComponent from "react-cytoscapejs";
import type { Core, ElementDefinition } from "cytoscape";

import type { PropagationGraphData } from "../types";

// Mock yayilim grafigi - gercek implementasyonda AnalysisDetail sayfasi,
// analiz sonucuna bagli PropagationGraph verisini backend'den (GNN analizi
// sonrasi) cekip buraya prop olarak gecirmelidir.
const MOCK_GRAPH: PropagationGraphData = {
  nodes: [
    { id: "post-1", type: "post" },
    { id: "post-2", type: "post" },
    { id: "post-3", type: "post" },
    { id: "post-4", type: "post" },
  ],
  edges: [
    { source: "post-1", target: "post-2" },
    { source: "post-1", target: "post-3" },
    { source: "post-2", target: "post-4" },
  ],
};

function toElements(data: PropagationGraphData): ElementDefinition[] {
  const nodeElements: ElementDefinition[] = data.nodes.map((node) => ({
    data: { id: node.id, label: node.id },
  }));
  const edgeElements: ElementDefinition[] = data.edges.map((edge, idx) => ({
    data: { id: `e${idx}`, source: edge.source, target: edge.target },
  }));
  return [...nodeElements, ...edgeElements];
}

const layout = { name: "cose", animate: false };

const stylesheet = [
  {
    selector: "node",
    style: {
      "background-color": "#4f46e5",
      label: "data(label)",
      color: "#1e293b",
      "font-size": "10px",
      width: 24,
      height: 24,
    },
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": "#94a3b8",
      "target-arrow-color": "#94a3b8",
      "target-arrow-shape": "triangle",
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
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-medium text-slate-600">
        Haber Yayilim Grafigi (propagation graph, mock veri)
      </h3>
      <CytoscapeComponent
        elements={elements}
        style={{ width: "100%", height: "360px" }}
        layout={layout}
        stylesheet={stylesheet}
        cy={(cy: Core) => {
          // TODO: gercek etkilesim (tiklama ile kullanici detayi gosterme vb.)
          cy.on("tap", "node", (evt) => {
            // eslint-disable-next-line no-console
            console.log("node tapped:", evt.target.id());
          });
        }}
      />
    </div>
  );
}
