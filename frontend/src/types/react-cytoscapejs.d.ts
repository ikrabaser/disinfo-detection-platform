declare module "react-cytoscapejs" {
  import type { ComponentType, CSSProperties } from "react";
  import type { Core, ElementDefinition } from "cytoscape";

  interface CytoscapeComponentProps {
    elements?: ElementDefinition[];
    style?: CSSProperties;
    layout?: Record<string, unknown>;
    stylesheet?: unknown[];
    cy?: (cy: Core) => void;
    [key: string]: unknown;
  }

  const CytoscapeComponent: ComponentType<CytoscapeComponentProps>;

  export default CytoscapeComponent;
}
