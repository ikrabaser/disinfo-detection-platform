import CytoscapeComponent from "react-cytoscapejs";
import type { Core, ElementDefinition } from "cytoscape";

import type { PropagationGraphData } from "../types";

interface Props {
  data?: PropagationGraphData;
}

function buildElements(data: PropagationGraphData): ElementDefinition[] {
  const nodeIds = data.nodes.map((node) => node.id);

  const incoming = new Map<string, number>();
  const outgoing = new Map<string, string[]>();

  nodeIds.forEach((id) => {
    incoming.set(id, 0);
    outgoing.set(id, []);
  });

  data.edges.forEach((edge) => {
    if (!incoming.has(edge.target) || !outgoing.has(edge.source)) {
      return;
    }

    incoming.set(
      edge.target,
      (incoming.get(edge.target) ?? 0) + 1
    );

    outgoing.get(edge.source)?.push(edge.target);
  });

  let roots = nodeIds.filter(
    (id) => (incoming.get(id) ?? 0) === 0
  );

  if (roots.length === 0 && nodeIds.length > 0) {
    roots = [nodeIds[0]];
  }

  const levels = new Map<string, number>();
  const queue: string[] = [];

  roots.forEach((root) => {
    levels.set(root, 0);
    queue.push(root);
  });

  while (queue.length > 0) {
    const current = queue.shift()!;
    const currentLevel = levels.get(current) ?? 0;

    for (const next of outgoing.get(current) ?? []) {
      if (!levels.has(next)) {
        levels.set(next, currentLevel + 1);
        queue.push(next);
      }
    }
  }

  nodeIds.forEach((id) => {
    if (!levels.has(id)) {
      levels.set(id, 0);
    }
  });

  const grouped = new Map<number, string[]>();

  nodeIds.forEach((id) => {
    const level = levels.get(id) ?? 0;

    if (!grouped.has(level)) {
      grouped.set(level, []);
    }

    grouped.get(level)!.push(id);
  });

  const maxLevel = Math.max(
    0,
    ...Array.from(levels.values())
  );

  const graphWidth = 900;
  const graphHeight = 320;
  const horizontalPadding = 70;
  const verticalPadding = 45;

  const positions = new Map<
    string,
    { x: number; y: number }
  >();

  grouped.forEach((ids, level) => {
    const x =
      maxLevel === 0
        ? graphWidth / 2
        : horizontalPadding +
          (level *
            (graphWidth - horizontalPadding * 2)) /
            maxLevel;

    const usableHeight =
      graphHeight - verticalPadding * 2;

    ids.forEach((id, index) => {
      const y =
        ids.length === 1
          ? graphHeight / 2
          : verticalPadding +
            (index * usableHeight) /
              Math.max(ids.length - 1, 1);

      positions.set(id, { x, y });
    });
  });

  const rootSet = new Set(roots);

  const nodes: ElementDefinition[] = data.nodes.map(
    (node) => ({
      data: {
        id: node.id,
        label: rootSet.has(node.id) ? "Kaynak" : "",
        root: rootSet.has(node.id) ? "true" : "false",
        nodeType: node.type ?? "post",
        nlpLabel:
          typeof node.attrs?.nlp_label === "string"
            ? node.attrs.nlp_label
            : "unknown",
      },
      position: positions.get(node.id),
    })
  );

  const edges: ElementDefinition[] = data.edges.map(
    (edge, index) => ({
      data: {
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
      },
    })
  );

  return [...nodes, ...edges];
}

const layout = {
  name: "preset",
  fit: true,
  padding: 45,
  animate: false,
};

const stylesheet = [
  {
    selector: "node",
    style: {
      "background-color": "#64748b",
      "border-color": "#ffffff",
      "border-width": 2,
      width: 18,
      height: 18,
      label: "data(label)",
      color: "#475569",
      "font-size": 10,
      "font-weight": 500,
      "text-valign": "bottom",
      "text-margin-y": 8,
    },
  },
  {
    selector: 'node[nlpLabel = "gercek"]',
    style: {
      "background-color": "#16a34a",
    },
  },
  {
    selector: 'node[nlpLabel = "belirsiz"]',
    style: {
      "background-color": "#d97706",
    },
  },
  {
    selector: 'node[nlpLabel = "sahte"]',
    style: {
      "background-color": "#dc2626",
    },
  },
  {
    selector: 'node[root = "true"]',
    style: {
      "border-color": "#0f172a",
      width: 28,
      height: 28,
      "border-width": 3,
    },
  },
  {
    selector: "edge",
    style: {
      width: 1.5,
      "line-color": "#cbd5e1",
      "target-arrow-color": "#94a3b8",
      "target-arrow-shape": "triangle",
      "arrow-scale": 0.75,
      "curve-style": "bezier",
    },
  },
];

export default function PropagationGraph({
  data,
}: Props) {
  if (!data) {
    return (
      <div className="flex h-[430px] items-center justify-center rounded-lg border border-slate-200 bg-white">
        <div className="text-center">
          <p className="text-sm font-medium text-slate-700">
            Yayılım ağı yükleniyor...
          </p>

          <p className="mt-1 text-xs text-slate-400">
            Backend verisi bekleniyor
          </p>
        </div>
      </div>
    );
  }

  const elements = buildElements(data);

  return (
    <div className="h-full overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="flex items-start justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            Yayılım Ağı
          </h3>

          <p className="mt-1 text-xs text-slate-500">
            İçeriğin paylaşım zinciri ve ilişkili hesap
            kümeleri
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

      <CytoscapeComponent
        elements={elements}
        layout={layout}
        stylesheet={stylesheet}
        style={{
          width: "100%",
          height: "360px",
          background: "#ffffff",
        }}
        cy={(cy: Core) => {
          cy.ready(() => {
            cy.fit(undefined, 45);
          });

          cy.on("tap", "node", (event) => {
            console.log(
              "Selected node:",
              event.target.id()
            );
          });
        }}
      />

      <div className="flex items-center gap-5 border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-green-600" />
          Güvenilir
        </span>

        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-amber-600" />
          Belirsiz
        </span>

        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
          Şüpheli
        </span>
      </div>
    </div>
  );
}
