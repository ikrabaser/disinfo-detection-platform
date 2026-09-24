import { Centrifuge } from "centrifuge";


const DEFAULT_CENTRIFUGO_WS_URL =
  import.meta.env.DEV
    ? "ws://localhost:8002/connection/websocket"
    : `${
        window.location.protocol === "https:"
          ? "wss"
          : "ws"
      }://${window.location.host}/connection/websocket`;

const CENTRIFUGO_WS_URL =
  import.meta.env.VITE_CENTRIFUGO_WS_URL ??
  DEFAULT_CENTRIFUGO_WS_URL;


export interface AnalysisProgressEvent {
  analysis_id: number;
  stage:
    | "started"
    | "nlp"
    | "graph"
    | "gnn"
    | "bot_detection"
    | "completed"
    | "failed"
    | string;
  progress: number;
}


interface SubscribeOptions {
  onProgress: (
    event: AnalysisProgressEvent
  ) => void;

  onSubscribed?: () => void | Promise<void>;
}


export function subscribeToAnalysisProgress(
  analysisId: number,
  options: SubscribeOptions
): () => void {
  const client = new Centrifuge(
    CENTRIFUGO_WS_URL
  );

  const channel = `analysis:${analysisId}`;

  const subscription =
    client.newSubscription(channel);

  subscription.on(
    "publication",
    (context) => {
      options.onProgress(
        context.data as AnalysisProgressEvent
      );
    }
  );

  subscription.on(
    "subscribed",
    () => {
      void options.onSubscribed?.();
    }
  );

  subscription.subscribe();
  client.connect();

  return () => {
    subscription.unsubscribe();
    client.disconnect();
  };
}
