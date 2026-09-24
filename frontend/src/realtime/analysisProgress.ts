import { Centrifuge } from "centrifuge";

import {
  apiClient,
} from "../api/client";


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

  onSubscribed?:
    () => void | Promise<void>;
}


async function getConnectionToken():
  Promise<string> {
  const { data } =
    await apiClient.get<{
      token: string;
    }>(
      "/realtime/connect-token/"
    );

  return data.token;
}


async function getSubscriptionToken(
  channel: string
): Promise<string> {
  const { data } =
    await apiClient.post<{
      token: string;
    }>(
      "/realtime/subscription-token/",
      {
        channel,
      }
    );

  return data.token;
}


export function subscribeToAnalysisProgress(
  analysisId: number,
  options: SubscribeOptions
): () => void {
  const client = new Centrifuge(
    CENTRIFUGO_WS_URL,
    {
      getToken:
        getConnectionToken,
    }
  );

  const channel =
    `analysis:${analysisId}`;

  const subscription =
    client.newSubscription(
      channel,
      {
        getToken: async (
          context
        ) =>
          getSubscriptionToken(
            context.channel
          ),
      }
    );

  subscription.on(
    "publication",
    (context) => {
      const event =
        context.data as AnalysisProgressEvent;

      options.onProgress(event);
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
