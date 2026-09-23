import {
  useMemo,
  useState,
} from "react";
import CytoscapeComponent from "react-cytoscapejs";

import type {
  Core,
  ElementDefinition,
} from "cytoscape";

import {
  CircleDot,
  Network,
} from "lucide-react";

import type {
  PropagationGraphData,
  PropagationNode,
} from "../types";


interface Props {
  data?: PropagationGraphData;
}


function buildElements(
  data: PropagationGraphData
): ElementDefinition[] {
  const nodeIds =
    data.nodes.map(
      (node) => node.id
    );

  const incoming =
    new Map<string, number>();

  const outgoing =
    new Map<string, string[]>();

  const degree =
    new Map<string, number>();

  nodeIds.forEach((id) => {
    incoming.set(id, 0);
    outgoing.set(id, []);
    degree.set(id, 0);
  });

  data.edges.forEach((edge) => {
    if (
      !incoming.has(edge.target) ||
      !outgoing.has(edge.source)
    ) {
      return;
    }

    incoming.set(
      edge.target,
      (incoming.get(
        edge.target
      ) ?? 0) + 1
    );

    outgoing.get(
      edge.source
    )?.push(
      edge.target
    );

    degree.set(
      edge.source,
      (degree.get(
        edge.source
      ) ?? 0) + 1
    );

    degree.set(
      edge.target,
      (degree.get(
        edge.target
      ) ?? 0) + 1
    );
  });

  let roots =
    nodeIds.filter(
      (id) =>
        (incoming.get(id) ?? 0)
        === 0
    );

  if (
    roots.length === 0 &&
    nodeIds.length > 0
  ) {
    roots = [
      nodeIds[0],
    ];
  }

  const levels =
    new Map<string, number>();

  const queue: string[] = [];

  roots.forEach((root) => {
    levels.set(root, 0);
    queue.push(root);
  });

  while (
    queue.length > 0
  ) {
    const current =
      queue.shift()!;

    const currentLevel =
      levels.get(
        current
      ) ?? 0;

    for (
      const next
      of outgoing.get(
        current
      ) ?? []
    ) {
      if (
        !levels.has(next)
      ) {
        levels.set(
          next,
          currentLevel + 1
        );

        queue.push(
          next
        );
      }
    }
  }

  nodeIds.forEach((id) => {
    if (
      !levels.has(id)
    ) {
      levels.set(id, 0);
    }
  });

  const grouped =
    new Map<
      number,
      string[]
    >();

  nodeIds.forEach((id) => {
    const level =
      levels.get(id) ?? 0;

    if (
      !grouped.has(level)
    ) {
      grouped.set(
        level,
        []
      );
    }

    grouped.get(
      level
    )!.push(id);
  });

  const maxLevel =
    Math.max(
      0,
      ...Array.from(
        levels.values()
      )
    );

  const graphWidth = 1050;
  const graphHeight = 330;

  const horizontalPadding =
    70;

  const verticalPadding =
    55;

  const positions =
    new Map<
      string,
      {
        x: number;
        y: number;
      }
    >();

  grouped.forEach(
    (
      ids,
      level
    ) => {
      const x =
        maxLevel === 0
          ? graphWidth / 2
          : horizontalPadding +
            (
              level *
              (
                graphWidth -
                horizontalPadding *
                  2
              )
            ) /
              maxLevel;

      const usableHeight =
        graphHeight -
        verticalPadding * 2;

      ids.forEach(
        (
          id,
          index
        ) => {
          const y =
            ids.length === 1
              ? graphHeight / 2
              : verticalPadding +
                (
                  index *
                  usableHeight
                ) /
                  Math.max(
                    ids.length - 1,
                    1
                  );

          positions.set(
            id,
            {
              x,
              y,
            }
          );
        }
      );
    }
  );

  const rootSet =
    new Set(roots);

  const nodes:
    ElementDefinition[] =
    data.nodes.map(
      (node) => {
        const nodeDegree =
          degree.get(
            node.id
          ) ?? 0;

        return {
          data: {
            id: node.id,

            label:
              rootSet.has(
                node.id
              )
                ? "Kaynak"
                : "",

            root:
              rootSet.has(
                node.id
              )
                ? "true"
                : "false",

            importance:
              nodeDegree >= 3
                ? "high"
                : nodeDegree >= 2
                  ? "medium"
                  : "normal",

            nodeType:
              node.type ??
              "post",

            nlpLabel:
              typeof node
                .attrs
                ?.nlp_label ===
                "string"
                ? node.attrs
                    .nlp_label
                : "unknown",
          },

          position:
            positions.get(
              node.id
            ),
        };
      }
    );

  const edges:
    ElementDefinition[] =
    data.edges.map(
      (
        edge,
        index
      ) => ({
        data: {
          id:
            `edge-${index}`,

          source:
            edge.source,

          target:
            edge.target,
        },
      })
    );

  return [
    ...nodes,
    ...edges,
  ];
}


const layout = {
  name: "preset",
  fit: true,
  padding: 48,
  animate: false,
};


const stylesheet = [
  {
    selector: "node",
    style: {
      "background-color":
        "#b9855b",

      "border-color":
        "#f7efe9",

      "border-width": 2,

      width: 18,
      height: 18,

      label:
        "data(label)",

      color:
        "#8b7d82",

      "font-size": 10,
      "font-weight": 500,

      "text-valign":
        "bottom",

      "text-margin-y":
        9,
    },
  },

  {
    selector:
      'node[importance = "medium"]',

    style: {
      width: 21,
      height: 21,
    },
  },

  {
    selector:
      'node[importance = "high"]',

    style: {
      width: 25,
      height: 25,
    },
  },

  {
    selector:
      'node[nlpLabel = "gercek"]',

    style: {
      "background-color":
        "#2f9c5a",
    },
  },

  {
    selector:
      'node[nlpLabel = "belirsiz"]',

    style: {
      "background-color":
        "#d97914",
    },
  },

  {
    selector:
      'node[nlpLabel = "sahte"]',

    style: {
      "background-color":
        "#d84c5d",
    },
  },

  {
    selector:
      'node[root = "true"]',

    style: {
      "border-color":
        "#2d2530",

      width: 30,
      height: 30,

      "border-width": 4,

      "background-color":
        "#d97914",
    },
  },

  {
    selector:
      "node:selected",

    style: {
      "border-color":
        "#ff895d",

      "border-width": 4,
    },
  },

  {
    selector: "edge",

    style: {
      width: 1.5,

      "line-color":
        "#b8b0ad",

      "target-arrow-color":
        "#a99f9c",

      "target-arrow-shape":
        "triangle",

      "arrow-scale":
        0.7,

      "curve-style":
        "bezier",

      opacity: 0.75,
    },
  },
];


function getNodeTitle(
  node: PropagationNode
): string {
  const username =
    node.attrs
      ?.author_username;

  if (
    typeof username ===
      "string" &&
    username
  ) {
    return `@${username}`;
  }

  return node.id;
}


export default function PropagationGraph({
  data,
}: Props) {
  const [
    selectedNodeId,
    setSelectedNodeId,
  ] =
    useState<
      string | null
    >(null);

  const selectedNode =
    useMemo(
      () =>
        data?.nodes.find(
          (node) =>
            node.id ===
            selectedNodeId
        ) ?? null,
      [
        data,
        selectedNodeId,
      ]
    );

  if (!data) {
    return (
      <div className="flex h-[430px] items-center justify-center rounded-xl border border-[#e7dfdc] bg-white dark:border-white/[0.08] dark:bg-[#1c1219]">
        <div className="text-center">
          <Network
            size={24}
            className="mx-auto text-[#b0a3a7] dark:text-[#695d63]"
          />

          <p className="mt-3 text-sm font-medium text-[#55474c] dark:text-[#d6c9ce]">
            Yayılım ağı yükleniyor...
          </p>

          <p className="mt-1 text-xs text-[#9a8d92] dark:text-[#786b71]">
            Backend verisi bekleniyor
          </p>
        </div>
      </div>
    );
  }

  const elements =
    buildElements(data);

  return (
    <section className="overflow-hidden rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="flex flex-col gap-3 border-b border-[#eee7e3] px-5 py-4 dark:border-white/[0.07] sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#f0cbbb] bg-[#fff2eb] text-[#c25b35] dark:border-[#ff895d]/15 dark:bg-[#ff895d]/[0.08] dark:text-[#ff956d]">
            <Network
              size={17}
              strokeWidth={1.8}
            />
          </div>

          <div>
            <h3 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              Yayılım Ağı
            </h3>

            <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
              İçeriğin gerçek yönlü paylaşım zinciri
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-right">
          <div>
            <p className="text-xs font-semibold text-[#594b50] dark:text-[#c5b7bc]">
              {data.nodes.length}
            </p>

            <p className="text-[10px] text-[#9a8d92] dark:text-[#786b71]">
              düğüm
            </p>
          </div>

          <div className="h-7 w-px bg-[#e8e1de] dark:bg-white/[0.07]" />

          <div>
            <p className="text-xs font-semibold text-[#594b50] dark:text-[#c5b7bc]">
              {data.edges.length}
            </p>

            <p className="text-[10px] text-[#9a8d92] dark:text-[#786b71]">
              bağlantı
            </p>
          </div>
        </div>
      </div>

      <div className="relative bg-[radial-gradient(circle_at_50%_45%,rgba(214,96,54,0.035),transparent_45%)] dark:bg-[radial-gradient(circle_at_50%_45%,rgba(255,137,93,0.035),transparent_42%)]">
        <CytoscapeComponent
          elements={elements}
          layout={layout}
          stylesheet={stylesheet}
          style={{
            width: "100%",
            height: "380px",
            background:
              "transparent",
          }}
          cy={(cy: Core) => {
            cy.ready(() => {
              cy.fit(
                undefined,
                52
              );
            });

            cy.on(
              "tap",
              "node",
              (event) => {
                setSelectedNodeId(
                  event.target.id()
                );
              }
            );

            cy.on(
              "tap",
              (event) => {
                if (
                  event.target ===
                  cy
                ) {
                  setSelectedNodeId(
                    null
                  );
                }
              }
            );
          }}
        />

        {selectedNode && (
          <div className="absolute bottom-4 left-4 w-[260px] rounded-xl border border-[#e7dfdc] bg-white/95 p-3.5 shadow-[0_16px_40px_rgba(40,25,31,0.10)] backdrop-blur dark:border-white/[0.09] dark:bg-[#22161e]/95 dark:shadow-[0_18px_45px_rgba(0,0,0,0.28)]">
            <div className="flex items-center gap-2">
              <CircleDot
                size={15}
                className="text-[#d96b3f] dark:text-[#ff895d]"
              />

              <p className="truncate text-xs font-semibold text-[#43363b] dark:text-[#eadde1]">
                {getNodeTitle(
                  selectedNode
                )}
              </p>
            </div>

            <p className="mt-2 text-[10px] text-[#95888d] dark:text-[#807279]">
              Node ID
            </p>

            <p className="mt-0.5 truncate font-mono text-[10px] text-[#67595e] dark:text-[#aa9ba1]">
              {
                selectedNode.id
              }
            </p>

            {typeof selectedNode
              .attrs
              ?.nlp_label ===
              "string" && (
              <>
                <p className="mt-2 text-[10px] text-[#95888d] dark:text-[#807279]">
                  NLP etiketi
                </p>

                <p className="mt-0.5 text-xs font-medium capitalize text-[#4b3e43] dark:text-[#cfc1c6]">
                  {
                    selectedNode
                      .attrs
                      .nlp_label
                  }
                </p>
              </>
            )}
          </div>
        )}
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-[#eee7e3] px-5 py-3 dark:border-white/[0.07]">
        <div className="flex flex-wrap items-center gap-5 text-[10px] text-[#84777c] dark:text-[#877980]">
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-[#2f9c5a]" />
            Güvenilir
          </span>

          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-[#d97914]" />
            Belirsiz
          </span>

          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-[#d84c5d]" />
            Şüpheli
          </span>
        </div>

        <span className="text-[10px] text-[#a09498] dark:text-[#6e6268]">
          Düğüme tıklayarak ayrıntıları görüntüleyin
        </span>
      </footer>
    </section>
  );
}
