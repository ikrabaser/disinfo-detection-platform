import {
  Bot,
  Check,
  Copy,
  FileSearch,
  Loader2,
  MessageSquareText,
  PanelLeft,
  Plus,
  Pencil,
  RotateCcw,
  Search,
  Send,
  Square,
  X,
  Trash2,
  UserRound,
  ChevronDown,
  CircleCheck,
  CircleX,
  Wrench,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  useSearchParams,
} from "react-router-dom";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  createAssistantConversation,
  deleteAssistantConversation,
  editAssistantUserMessage,
  getAgentProviders,
  getAssistantConversation,
  listAssistantConversations,
  regenerateAssistantResponse,
  renameAssistantConversation,
  type AgentProvider,
  type AssistantConversation,
  type AssistantConversationSummary,
  type AssistantMessage,
} from "../api/client";

import {
  sendAssistantMessageStream,
  type AssistantToolCall,
} from "../api/assistantStream";


function getErrorMessage(
  error: unknown
): string {
  if (
    error instanceof Error
    && error.message
  ) {
    return error.message;
  }

  if (
    typeof error === "object"
    && error !== null
    && "response" in error
  ) {
    const response = (
      error as {
        response?: {
          data?: {
            detail?: string;
          };
        };
      }
    ).response;

    if (
      typeof response?.data?.detail
      === "string"
    ) {
      return response.data.detail;
    }
  }

  return (
    "Assistant isteği tamamlanamadı."
  );
}


interface MessageToolCall {
  id?: string;
  name: string;
  status?: string;
}


function toolDisplayName(
  name: string
): string {
  switch (name) {
    case "search_evidence":
      return "Kanıt arama";

    case "get_analysis_result":
      return "Analiz sonucu";

    case "run_gnn_analysis":
      return "GNN analizi";

    case "run_bot_analysis":
      return "Bot analizi";

    case "run_nlp_analysis":
      return "NLP analizi";

    case "verify_sources":
      return "Kaynak doğrulama";

    case "get_news":
      return "Haber verisi";

    case "get_social_posts":
      return "Sosyal medya verisi";

    default:
      return name
        .replace(/_/g, " ");
  }
}


function getMessageToolCalls(
  metadata: Record<string, unknown>
): MessageToolCall[] {
  const raw =
    metadata.tool_calls;

  if (!Array.isArray(raw)) {
    return [];
  }

  return raw.flatMap(
    (item) => {
      if (
        typeof item !== "object"
        || item === null
      ) {
        return [];
      }

      const record =
        item as Record<
          string,
          unknown
        >;

      if (
        typeof record.name
        !== "string"
      ) {
        return [];
      }

      return [
        {
          id:
            typeof record.id
            === "string"
              ? record.id
              : undefined,
          name: record.name,
          status:
            typeof record.status
            === "string"
              ? record.status
              : undefined,
        },
      ];
    }
  );
}


function toolStatusText(
  toolCall: AssistantToolCall
): string {
  switch (toolCall.name) {
    case "search_evidence":
      return "Kanıtlar aranıyor";

    case "get_analysis_result":
      return "Analiz sonucu inceleniyor";

    case "run_gnn_analysis":
      return "GNN analizi çalıştırılıyor";

    case "run_bot_analysis":
      return "Bot analizi çalıştırılıyor";

    default:
      return "VERITAS aracı çalışıyor";
  }
}


function providerDisplayName(
  providerName: string
): string {
  switch (
    providerName.toLowerCase()
  ) {
    case "anthropic":
    case "claude":
      return "Claude";

    case "openai":
      return "OpenAI";

    case "evren":
      return "EVREN";

    default:
      return providerName;
  }
}


function formatConversationDate(
  value: string
): string {
  return new Intl.DateTimeFormat(
    "tr-TR",
    {
      day: "2-digit",
      month: "short",
    }
  ).format(
    new Date(value)
  );
}


function MarkdownContent({
  content,
  streaming = false,
}: {
  content: string;
  streaming?: boolean;
}) {
  return (
    <div
      className={[
        "min-w-0 text-[14px] leading-7",
        "text-[#43373b] dark:text-[#e8dde1]",
        "[&_p]:my-3 [&_p:first-child]:mt-0",
        "[&_p:last-child]:mb-0",
        "[&_h1]:mb-4 [&_h1]:mt-6",
        "[&_h1]:text-xl [&_h1]:font-semibold",
        "[&_h2]:mb-3 [&_h2]:mt-6",
        "[&_h2]:text-lg [&_h2]:font-semibold",
        "[&_h3]:mb-2 [&_h3]:mt-5",
        "[&_h3]:text-base [&_h3]:font-semibold",
        "[&_strong]:font-semibold",
        "[&_strong]:text-[#2f2529]",
        "dark:[&_strong]:text-[#fff5f2]",
        "[&_ul]:my-3 [&_ul]:list-disc",
        "[&_ul]:space-y-1 [&_ul]:pl-6",
        "[&_ol]:my-3 [&_ol]:list-decimal",
        "[&_ol]:space-y-1 [&_ol]:pl-6",
        "[&_blockquote]:my-4",
        "[&_blockquote]:border-l-2",
        "[&_blockquote]:border-[#d8cbc6]",
        "[&_blockquote]:pl-4",
        "[&_blockquote]:text-[#76686d]",
        "dark:[&_blockquote]:border-white/15",
        "dark:[&_blockquote]:text-[#a99ba1]",
        "[&_a]:font-medium",
        "[&_a]:text-[#b75634]",
        "[&_a]:underline",
        "[&_a]:underline-offset-2",
        "dark:[&_a]:text-[#ff9870]",
        "[&_code]:rounded-md",
        "[&_code]:bg-[#f2eeec]",
        "[&_code]:px-1.5 [&_code]:py-0.5",
        "[&_code]:font-mono",
        "[&_code]:text-[12px]",
        "dark:[&_code]:bg-white/[0.07]",
        "[&_pre]:my-4 [&_pre]:overflow-auto",
        "[&_pre]:rounded-xl",
        "[&_pre]:bg-[#191317]",
        "[&_pre]:p-4",
        "[&_pre]:text-[#eee5e8]",
        "[&_pre_code]:bg-transparent",
        "[&_pre_code]:p-0",
        "[&_table]:my-4 [&_table]:w-full",
        "[&_table]:border-collapse",
        "[&_th]:border",
        "[&_th]:border-[#e3dad6]",
        "[&_th]:bg-[#f7f4f2]",
        "[&_th]:px-3 [&_th]:py-2",
        "[&_th]:text-left",
        "[&_th]:text-xs",
        "[&_td]:border",
        "[&_td]:border-[#e3dad6]",
        "[&_td]:px-3 [&_td]:py-2",
        "[&_td]:align-top",
        "[&_td]:text-xs",
        "dark:[&_th]:border-white/[0.09]",
        "dark:[&_th]:bg-white/[0.04]",
        "dark:[&_td]:border-white/[0.09]",
      ].join(" ")}
    >
      <ReactMarkdown
        remarkPlugins={[
          remarkGfm,
        ]}
      >
        {content}
      </ReactMarkdown>

      {streaming && (
        <span
          className="
            ml-1 inline-block h-4
            w-[2px] animate-pulse
            bg-[#c86038] align-middle
            dark:bg-[#ff895d]
          "
        />
      )}
    </div>
  );
}


const GENERAL_SUGGESTIONS = [
  "VERITAS sisteminin analiz akışını açıkla.",
  "GNN ve bot analizi arasındaki fark nedir?",
  "Bir dezenformasyon analizinde hangi sinyallere bakmalıyım?",
  "Evidence ve model skorları birlikte nasıl yorumlanmalı?",
];


const ANALYSIS_SUGGESTIONS = [
  "Bu analizi kısa ve anlaşılır şekilde özetle.",
  "GNN ve bot sonuçlarını karşılaştır.",
  "Bu analizde hangi model sonuçları güncel?",
  "Sonuçların sınırlamalarını teknik olarak açıkla.",
];


export default function Assistant() {
  const [searchParams] =
    useSearchParams();

  const analysisParam =
    searchParams.get("analysis");

  const analysisId =
    analysisParam
    && Number.isFinite(
      Number(analysisParam)
    )
      ? Number(analysisParam)
      : null;


  const [
    providers,
    setProviders,
  ] = useState<AgentProvider[]>([]);

  const [
    conversations,
    setConversations,
  ] = useState<
    AssistantConversationSummary[]
  >([]);

  const [
    conversation,
    setConversation,
  ] = useState<
    AssistantConversation | null
  >(null);

  const [
    selectedProvider,
    setSelectedProvider,
  ] = useState("openai");

  const [
    draft,
    setDraft,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    sending,
    setSending,
  ] = useState(false);

  const [
    streamingText,
    setStreamingText,
  ] = useState("");

  const [
    toolStatus,
    setToolStatus,
  ] = useState<string | null>(
    null
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  const [
    historyQuery,
    setHistoryQuery,
  ] = useState("");

  const [
    copiedMessageId,
    setCopiedMessageId,
  ] = useState<number | null>(
    null
  );


  const [
    regenerating,
    setRegenerating,
  ] = useState(false);


  const [
    editingMessageId,
    setEditingMessageId,
  ] = useState<number | null>(
    null
  );

  const [
    editDraft,
    setEditDraft,
  ] = useState("");

  const [
    editingMessageSending,
    setEditingMessageSending,
  ] = useState(false);


  const [
    renaming,
    setRenaming,
  ] = useState(false);

  const [
    renameDraft,
    setRenameDraft,
  ] = useState("");

  const messagesEndRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const messagesScrollRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const [
    isAtBottom,
    setIsAtBottom,
  ] = useState(true);

  const [
    newResponseAvailable,
    setNewResponseAvailable,
  ] = useState(false);

  const textareaRef =
    useRef<HTMLTextAreaElement | null>(
      null
    );


  const streamAbortRef =
    useRef<AbortController | null>(
      null
    );

  const [
    mobileHistoryOpen,
    setMobileHistoryOpen,
  ] = useState(false);


  const filteredConversations =
    useMemo(
      () => {
        const query =
          historyQuery
            .trim()
            .toLocaleLowerCase(
              "tr-TR"
            );

        if (!query) {
          return conversations;
        }

        return conversations.filter(
          (item) =>
            item.title
              .toLocaleLowerCase(
                "tr-TR"
              )
              .includes(query)
        );
      },
      [
        conversations,
        historyQuery,
      ]
    );


  const activeProvider =
    providers.find(
      (item) =>
        item.name ===
        selectedProvider
    );


  const suggestions =
    analysisId
      ? ANALYSIS_SUGGESTIONS
      : GENERAL_SUGGESTIONS;


  async function refreshConversations() {
    const data =
      await listAssistantConversations();

    setConversations(data);
  }


  useEffect(() => {
    let cancelled = false;

    Promise.all([
      getAgentProviders(),
      listAssistantConversations(),
    ])
      .then(
        ([
          providerData,
          conversationData,
        ]) => {
          if (cancelled) {
            return;
          }

          setProviders(
            providerData
          );

          setConversations(
            conversationData
          );

          const configured =
            providerData.find(
              (item) =>
                item.configured
            );

          if (configured) {
            setSelectedProvider(
              configured.name
            );
          } else if (
            providerData[0]
          ) {
            setSelectedProvider(
              providerData[0].name
            );
          }
        }
      )
      .catch(() => {
        if (!cancelled) {
          setError(
            "Assistant verileri yüklenemedi."
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);


  useEffect(() => {
    const element =
      textareaRef.current;

    if (!element) {
      return;
    }

    element.style.height =
      "0px";

    element.style.height =
      `${Math.min(
        element.scrollHeight,
        180
      )}px`;
  }, [draft]);


  useEffect(() => {
    if (!isAtBottom) {
      if (
        sending
        && streamingText
      ) {
        setNewResponseAvailable(
          true
        );
      }

      return;
    }

    const frame =
      window.requestAnimationFrame(
        () => {
          const element =
            messagesScrollRef.current;

          if (!element) {
            return;
          }

          element.scrollTo({
            top: element.scrollHeight,
            behavior: sending
              ? "smooth"
              : "auto",
          });
        }
      );

    return () => {
      window.cancelAnimationFrame(
        frame
      );
    };
  }, [
    conversation?.id,
    conversation?.messages.length,
    streamingText,
    toolStatus,
    sending,
    isAtBottom,
  ]);


  function handleMessagesScroll() {
    const element =
      messagesScrollRef.current;

    if (!element) {
      return;
    }

    const distanceFromBottom =
      element.scrollHeight
      - element.scrollTop
      - element.clientHeight;

    const atBottom =
      distanceFromBottom < 96;

    setIsAtBottom(
      atBottom
    );

    if (atBottom) {
      setNewResponseAvailable(
        false
      );
    }
  }


  function scrollToLatest(
    behavior: ScrollBehavior = "smooth"
  ) {
    const element =
      messagesScrollRef.current;

    if (!element) {
      return;
    }

    element.scrollTo({
      top: element.scrollHeight,
      behavior,
    });

    setIsAtBottom(true);

    setNewResponseAvailable(
      false
    );
  }


  async function openConversation(
    id: string
  ) {
    if (sending) {
      return;
    }

    setError(null);

    try {
      const data =
        await getAssistantConversation(
          id
        );

      setConversation(data);

      setIsAtBottom(true);
      setNewResponseAvailable(false);

      setMobileHistoryOpen(false);

      setSelectedProvider(
        data.provider
      );

      setDraft("");
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError
        )
      );
    }
  }


  function startNewChat() {
    if (sending) {
      return;
    }

    setConversation(null);
    setDraft("");
    setError(null);

    setIsAtBottom(true);
    setNewResponseAvailable(false);

    setMobileHistoryOpen(false);
    setStreamingText("");
    setToolStatus(null);

    const configured =
      providers.find(
        (item) =>
          item.configured
      );

    if (configured) {
      setSelectedProvider(
        configured.name
      );
    }
  }


  function beginRename() {
    if (!conversation) {
      return;
    }

    setRenameDraft(
      conversation.title
    );

    setRenaming(true);
  }


  async function submitRename() {
    if (!conversation) {
      return;
    }

    const title =
      renameDraft.trim();

    if (!title) {
      return;
    }

    try {
      const updated =
        await renameAssistantConversation(
          conversation.id,
          title
        );

      setConversation(
        updated
      );

      setRenaming(false);

      await refreshConversations();
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError
        )
      );
    }
  }


  async function handleDelete() {
    if (
      !conversation
      || sending
    ) {
      return;
    }

    const confirmed =
      window.confirm(
        "Bu sohbet silinsin mi?"
      );

    if (!confirmed) {
      return;
    }

    try {
      await deleteAssistantConversation(
        conversation.id
      );

      setConversation(null);

      await refreshConversations();
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError
        )
      );
    }
  }


  function beginMessageEdit(
    message: AssistantMessage
  ) {
    if (
      sending
      || regenerating
      || editingMessageSending
    ) {
      return;
    }

    setEditingMessageId(
      message.id
    );

    setEditDraft(
      message.content
    );

    setError(null);
  }


  function cancelMessageEdit() {
    setEditingMessageId(null);
    setEditDraft("");
  }


  async function submitMessageEdit() {
    if (
      !conversation
      || editingMessageId === null
      || sending
      || regenerating
      || editingMessageSending
    ) {
      return;
    }

    const content =
      editDraft.trim();

    if (!content) {
      return;
    }

    setEditingMessageSending(
      true
    );

    setError(null);

    try {
      await editAssistantUserMessage(
        conversation.id,
        editingMessageId,
        content
      );

      const refreshed =
        await getAssistantConversation(
          conversation.id
        );

      setConversation(
        refreshed
      );

      setEditingMessageId(null);
      setEditDraft("");

      await refreshConversations();

    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError
        )
      );

    } finally {
      setEditingMessageSending(
        false
      );
    }
  }


  async function handleRegenerate() {
    if (
      !conversation
      || sending
      || regenerating
    ) {
      return;
    }

    setRegenerating(true);
    setError(null);

    try {
      const result =
        await regenerateAssistantResponse(
          conversation.id
        );

      setConversation(
        (previous) => {
          if (!previous) {
            return previous;
          }

          return {
            ...previous,
            messages:
              previous.messages.map(
                (message) =>
                  message.id
                    === result
                      .replaced_message_id
                    ? result
                        .assistant_message
                    : message
              ),
          };
        }
      );

      await refreshConversations();

    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError
        )
      );

    } finally {
      setRegenerating(false);
    }
  }


  async function handleCopy(
    messageId: number,
    content: string
  ) {
    try {
      await navigator.clipboard.writeText(
        content
      );

      setCopiedMessageId(
        messageId
      );

      window.setTimeout(
        () => {
          setCopiedMessageId(
            (current) =>
              current === messageId
                ? null
                : current
          );
        },
        1600
      );
    } catch {
      setError(
        "Mesaj panoya kopyalanamadı."
      );
    }
  }


  async function handleSend(
    contentOverride?: string
  ) {
    const content = (
      contentOverride ??
      draft
    ).trim();

    if (
      !content
      || sending
    ) {
      return;
    }

    setIsAtBottom(true);
    setNewResponseAvailable(false);

    setSending(true);
    setError(null);
    setStreamingText("");

    setToolStatus(
      "Yanıt hazırlanıyor"
    );

    let activeConversation =
      conversation;

    try {
      if (!activeConversation) {
        activeConversation =
          await createAssistantConversation(
            {
              provider:
                selectedProvider,
              analysis_id:
                analysisId,
            }
          );

        setConversation(
          activeConversation
        );
      }

      const current =
        activeConversation;

      setDraft("");

      const abortController =
        new AbortController();

      streamAbortRef.current =
        abortController;

      await sendAssistantMessageStream(
        current.id,
        content,
        {
          onStart: (
            userMessage
          ) => {
            setConversation(
              (previous) => {
                const base =
                  previous ??
                  current;

                const exists =
                  base.messages.some(
                    (message) =>
                      message.id
                      === userMessage.id
                  );

                if (exists) {
                  return base;
                }

                return {
                  ...base,
                  messages: [
                    ...base.messages,
                    userMessage,
                  ],
                };
              }
            );
          },

          onDelta: (
            delta
          ) => {
            setToolStatus(null);

            setStreamingText(
              (previous) =>
                previous + delta
            );
          },

          onToolStart: (
            toolCall
          ) => {
            setToolStatus(
              toolStatusText(
                toolCall
              )
            );
          },

          onToolEnd: () => {
            setToolStatus(
              "Yanıt oluşturuluyor"
            );
          },

          onDone: (
            userMessage,
            assistantMessage
          ) => {
            setConversation(
              (previous) => {
                const base =
                  previous ??
                  current;

                const cleanMessages =
                  base.messages.filter(
                    (message) =>
                      message.id
                        !==
                        userMessage.id
                      &&
                      message.id
                        !==
                        assistantMessage.id
                  );

                return {
                  ...base,
                  messages: [
                    ...cleanMessages,
                    userMessage,
                    assistantMessage,
                  ],
                };
              }
            );

            setStreamingText("");
            setToolStatus(null);
          },
        },
        abortController.signal
      );

      const refreshed =
        await getAssistantConversation(
          current.id
        );

      setConversation(
        refreshed
      );

      await refreshConversations();

    } catch (requestError) {
      const aborted =
        requestError instanceof DOMException
        && requestError.name
          === "AbortError";

      if (!aborted) {
        setError(
          getErrorMessage(
            requestError
          )
        );
      }

      if (activeConversation) {
        const refreshed =
          await getAssistantConversation(
            activeConversation.id
          ).catch(
            () => null
          );

        if (refreshed) {
          setConversation(
            refreshed
          );
        }
      }

    } finally {
      streamAbortRef.current = null;

      setStreamingText("");
      setToolStatus(null);
      setSending(false);
    }
  }


  function handleStop() {
    streamAbortRef.current?.abort();
  }


  const hasMessages =
    (
      conversation?.messages
        .length ??
      0
    ) > 0;


  return (
    <div
      className="
        mx-auto flex
        h-[calc(100vh-124px)]
        min-h-[640px]
        w-full max-w-[1600px]
        overflow-hidden rounded-2xl
        border border-[#e7dfdc]
        bg-white
        shadow-soft-panel
        dark:border-white/[0.08]
        dark:bg-[#171016]
        dark:shadow-dark-panel
      "
    >
      {mobileHistoryOpen && (
        <button
          type="button"
          aria-label="Sohbet geçmişini kapat"
          onClick={() =>
            setMobileHistoryOpen(false)
          }
          className="
            fixed inset-0 z-40
            bg-black/30 backdrop-blur-[1px]
            lg:hidden
          "
        />
      )}

      <aside
        className={[
          "fixed inset-y-0 left-0 z-50",
          "flex w-[280px] shrink-0 flex-col",
          "border-r border-[#ebe4e1]",
          "bg-[#f9f7f5]",
          "transition-transform duration-200",
          "lg:relative lg:inset-auto lg:z-auto",
          "lg:translate-x-0",
          "dark:border-white/[0.07]",
          "dark:bg-[#130d12]",
          mobileHistoryOpen
            ? "translate-x-0"
            : "-translate-x-full",
        ].join(" ")}
      >
        <div className="p-3">
          <button
            type="button"
            onClick={
              startNewChat
            }
            disabled={sending}
            className="
              flex h-10 w-full
              items-center gap-2
              rounded-lg px-3
              text-xs font-medium
              text-[#514348]
              transition
              hover:bg-[#eee9e6]
              disabled:opacity-50
              dark:text-[#d8ccd0]
              dark:hover:bg-white/[0.05]
            "
          >
            <Plus
              size={16}
              strokeWidth={1.8}
            />

            Yeni sohbet
          </button>

          <div className="relative mt-2">
            <Search
              size={14}
              className="
                absolute left-3 top-1/2
                -translate-y-1/2
                text-[#a19498]
                dark:text-[#675c61]
              "
            />

            <input
              value={historyQuery}
              onChange={(event) =>
                setHistoryQuery(
                  event.target.value
                )
              }
              placeholder="Sohbetlerde ara"
              className="
                h-9 w-full rounded-lg
                border border-transparent
                bg-[#f0ece9]
                pl-9 pr-3
                text-[11px]
                text-[#514449]
                outline-none
                transition
                placeholder:text-[#a4999d]
                focus:border-[#d7cbc6]
                focus:bg-white
                dark:bg-white/[0.04]
                dark:text-[#cfc2c7]
                dark:placeholder:text-[#675b61]
                dark:focus:border-white/[0.09]
                dark:focus:bg-white/[0.055]
              "
            />
          </div>
        </div>

        <div
          className="
            flex-1 overflow-y-auto
            px-2 pb-3
          "
        >
          <p
            className="
              px-3 pb-2 pt-3
              text-[9px] font-semibold
              uppercase tracking-[0.12em]
              text-[#a19599]
              dark:text-[#62575c]
            "
          >
            Sohbetler
          </p>

          {filteredConversations.length ===
            0 && (
            <p
              className="
                px-3 py-6 text-center
                text-[11px]
                text-[#9b8f93]
                dark:text-[#71656b]
              "
            >
              {historyQuery
                ? "Eşleşen sohbet yok."
                : "Henüz sohbet yok."}
            </p>
          )}

          {filteredConversations.map(
            (item) => {
              const active =
                conversation?.id ===
                item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  disabled={sending}
                  onClick={() =>
                    void openConversation(
                      item.id
                    )
                  }
                  className={[
                    "group mb-1 w-full",
                    "rounded-lg px-3 py-2.5",
                    "text-left transition",
                    "disabled:opacity-50",
                    active
                      ? (
                        "bg-white shadow-sm "
                        + "dark:bg-white/[0.06] "
                        + "dark:shadow-none"
                      )
                      : (
                        "hover:bg-[#eee9e6] "
                        + "dark:hover:bg-white/[0.035]"
                      ),
                  ].join(" ")}
                >
                  <p
                    className="
                      truncate text-[12px]
                      font-medium
                      text-[#514449]
                      dark:text-[#d3c7cb]
                    "
                  >
                    {item.title}
                  </p>

                  <div
                    className="
                      mt-1 flex items-center
                      justify-between gap-2
                      text-[9px]
                      text-[#9f9296]
                      dark:text-[#6d6167]
                    "
                  >
                    <span>
                      {providerDisplayName(
                        item.provider
                      )}
                      {" · "}
                      {item.message_count}
                    </span>

                    <span>
                      {formatConversationDate(
                        item.updated_at
                      )}
                    </span>
                  </div>
                </button>
              );
            }
          )}
        </div>
      </aside>

      <section
        className="
          relative
          flex min-w-0 flex-1
          flex-col bg-white
          dark:bg-[#171016]
        "
      >
        <header
          className="
            flex min-h-[58px]
            items-center
            justify-between gap-3
            border-b
            border-[#eee8e5]
            px-4 sm:px-5
            dark:border-white/[0.06]
          "
        >
          <div className="group flex min-w-0 items-center gap-2">
            <button
              type="button"
              onClick={() =>
                setMobileHistoryOpen(true)
              }
              className="
                flex h-8 w-8
                items-center justify-center
                rounded-lg
                text-[#74666b]
                transition
                hover:bg-[#f2edeb]
                lg:hidden
                dark:text-[#a89aa0]
                dark:hover:bg-white/[0.05]
              "
              title="Sohbet geçmişi"
            >
              <PanelLeft size={16} />
            </button>

            <MessageSquareText
              size={16}
              className="
                hidden text-[#c86038]
                sm:block
                dark:text-[#ff895d]
              "
            />

            <div className="min-w-0">
              {renaming && conversation ? (
                <div className="flex items-center gap-1.5">
                  <input
                    autoFocus
                    value={renameDraft}
                    onChange={(event) =>
                      setRenameDraft(
                        event.target.value
                      )
                    }
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter"
                      ) {
                        event.preventDefault();
                        void submitRename();
                      }

                      if (
                        event.key === "Escape"
                      ) {
                        setRenaming(false);
                      }
                    }}
                    className="
                      h-8 w-[260px]
                      rounded-lg border
                      border-[#d8ccc7]
                      bg-white px-2.5
                      text-[12px]
                      font-medium
                      text-[#302529]
                      outline-none
                      focus:border-[#bca59b]
                      dark:border-white/[0.12]
                      dark:bg-white/[0.05]
                      dark:text-[#f5ebee]
                    "
                  />

                  <button
                    type="button"
                    onClick={() =>
                      void submitRename()
                    }
                    className="
                      flex h-7 w-7
                      items-center
                      justify-center
                      rounded-md
                      text-[#6c5d62]
                      hover:bg-[#f1ece9]
                      dark:text-[#aa9da2]
                      dark:hover:bg-white/[0.05]
                    "
                  >
                    <Check size={13} />
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setRenaming(false)
                    }
                    className="
                      flex h-7 w-7
                      items-center
                      justify-center
                      rounded-md
                      text-[#8e8085]
                      hover:bg-[#f1ece9]
                      dark:text-[#75686e]
                      dark:hover:bg-white/[0.05]
                    "
                  >
                    <X size={13} />
                  </button>
                </div>
              ) : (
                <div className="flex min-w-0 items-center gap-1.5">
                  <p
                    className="
                      truncate text-[13px]
                      font-semibold
                      text-[#302529]
                      dark:text-[#f5ebee]
                    "
                  >
                    {conversation?.title ||
                      "VERITAS Assistant"}
                  </p>

                  {conversation && (
                    <button
                      type="button"
                      onClick={beginRename}
                      disabled={sending}
                      className="
                        flex h-6 w-6
                        shrink-0 items-center
                        justify-center
                        rounded-md
                        text-[#a19498]
                        opacity-0
                        transition
                        hover:bg-[#f1ece9]
                        hover:text-[#66575c]
                        group-hover:opacity-100
                        focus:opacity-100
                        dark:text-[#6e6267]
                        dark:hover:bg-white/[0.05]
                        dark:hover:text-[#aaa0a4]
                      "
                      title="Sohbet adını değiştir"
                    >
                      <Pencil size={11} />
                    </button>
                  )}
                </div>
              )}

              {(conversation?.analysis ||
                analysisId) && (
                <div
                  className="
                    mt-0.5 flex items-center
                    gap-1 text-[9px]
                    text-[#9a8c91]
                    dark:text-[#70636a]
                  "
                >
                  <FileSearch
                    size={10}
                  />

                  Analysis #
                  {conversation?.analysis ??
                    analysisId}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={
                providers.length
                  ? selectedProvider
                  : ""
              }
              disabled={
                conversation !== null
                || loading
                || providers.length === 0
              }
              onChange={(event) =>
                setSelectedProvider(
                  event.target.value
                )
              }
              className="
                max-w-[190px]
                rounded-lg border
                border-transparent
                bg-transparent
                px-2 py-1.5
                text-[11px] font-medium
                text-[#65575c]
                outline-none transition
                hover:bg-[#f4f0ee]
                focus:border-[#dbd1cc]
                disabled:opacity-80
                dark:text-[#b8abb0]
                dark:hover:bg-white/[0.045]
                dark:focus:border-white/[0.09]
              "
            >
              {providers.length === 0 && (
                <option
                  value=""
                  disabled
                >
                  {loading
                    ? "Yükleniyor..."
                    : "Model yok"}
                </option>
              )}

              {providers.map(
                (provider) => (
                  <option
                    key={
                      provider.name
                    }
                    value={
                      provider.name
                    }
                    disabled={
                      !provider.configured
                    }
                  >
                    {providerDisplayName(
                      provider.name
                    )}
                    {" · "}
                    {provider.model ||
                      "model"}
                    {!provider.configured
                      ? " (bağlı değil)"
                      : ""}
                  </option>
                )
              )}
            </select>

            {conversation && (
              <button
                type="button"
                onClick={() =>
                  void handleDelete()
                }
                disabled={sending}
                className="
                  flex h-8 w-8
                  items-center justify-center
                  rounded-lg
                  text-[#9f8f94]
                  transition
                  hover:bg-red-50
                  hover:text-red-600
                  disabled:opacity-40
                  dark:text-[#786b71]
                  dark:hover:bg-red-400/[0.07]
                  dark:hover:text-red-300
                "
                title="Sohbeti sil"
              >
                <Trash2
                  size={15}
                />
              </button>
            )}
          </div>
        </header>

        <div
          ref={
            messagesScrollRef
          }
          onScroll={
            handleMessagesScroll
          }
          className="
            min-h-0 flex-1
            overflow-y-auto
          "
        >
          {loading ? (
            <div
              className="
                flex h-full
                items-center
                justify-center
                gap-2 text-xs
                text-[#9b8e93]
                dark:text-[#776b70]
              "
            >
              <Loader2
                size={15}
                className="animate-spin"
              />

              Assistant yükleniyor
            </div>
          ) : (
            <div
              className="
                mx-auto flex
                min-h-full w-full
                max-w-[860px]
                flex-col
                px-4 pb-8 pt-8
                sm:px-6
              "
            >
              {!hasMessages
                && !sending ? (
                <div
                  className="
                    my-auto flex
                    flex-col items-center
                    py-12 text-center
                  "
                >
                  <div
                    className="
                      flex h-11 w-11
                      items-center
                      justify-center
                      rounded-full
                      border border-[#eaded9]
                      bg-[#faf7f5]
                      text-[#b85836]
                      dark:border-white/[0.08]
                      dark:bg-white/[0.04]
                      dark:text-[#ff956e]
                    "
                  >
                    <Bot
                      size={21}
                      strokeWidth={1.7}
                    />
                  </div>

                  <h1
                    className="
                      mt-5 text-2xl
                      font-semibold
                      tracking-[-0.025em]
                      text-[#302529]
                      dark:text-[#f7edef]
                    "
                  >
                    Size nasıl yardımcı
                    olabilirim?
                  </h1>

                  <p
                    className="
                      mt-2 max-w-[520px]
                      text-[12px]
                      leading-5
                      text-[#8f8287]
                      dark:text-[#82757b]
                    "
                  >
                    VERITAS analizlerini,
                    kanıtları, model
                    sinyallerini ve
                    provenance bilgisini
                    birlikte inceleyebilirim.
                  </p>

                  {analysisId && (
                    <div
                      className="
                        mt-4 inline-flex
                        items-center gap-2
                        rounded-full
                        border
                        border-[#e8deda]
                        bg-[#faf8f6]
                        px-3 py-1.5
                        text-[10px]
                        text-[#74666c]
                        dark:border-white/[0.07]
                        dark:bg-white/[0.03]
                        dark:text-[#998b91]
                      "
                    >
                      <FileSearch
                        size={12}
                      />

                      Analysis #{analysisId}
                      bağlamı aktif
                    </div>
                  )}

                  <div
                    className="
                      mt-8 grid w-full
                      max-w-[680px]
                      gap-2
                      sm:grid-cols-2
                    "
                  >
                    {suggestions.map(
                      (suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() =>
                            void handleSend(
                              suggestion
                            )
                          }
                          className="
                            rounded-xl border
                            border-[#e7dfdc]
                            bg-white px-4 py-3
                            text-left text-[11px]
                            leading-5
                            text-[#695b60]
                            transition
                            hover:border-[#d7c8c2]
                            hover:bg-[#faf7f5]
                            dark:border-white/[0.07]
                            dark:bg-white/[0.025]
                            dark:text-[#a99ca1]
                            dark:hover:border-white/[0.12]
                            dark:hover:bg-white/[0.045]
                          "
                        >
                          {suggestion}
                        </button>
                      )
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-8">
                  {conversation?.messages.map(
                    (message) => {
                      const isUser =
                        message.role ===
                        "user";

                      const messageToolCalls =
                        isUser
                          ? []
                          : getMessageToolCalls(
                              message.metadata
                            );

                      if (isUser) {
                        const isEditing =
                          editingMessageId
                          === message.id;

                        return (
                          <div
                            key={
                              message.id
                            }
                            className="
                              group flex
                              justify-end
                            "
                          >
                            <div
                              className="
                                flex w-full
                                max-w-[78%]
                                items-start gap-2
                              "
                            >
                              <div
                                className="
                                  min-w-0 flex-1
                                "
                              >
                                {isEditing ? (
                                  <div
                                    className="
                                      rounded-2xl
                                      border
                                      border-[#d9cec9]
                                      bg-[#faf8f6]
                                      p-2
                                      dark:border-white/[0.11]
                                      dark:bg-white/[0.05]
                                    "
                                  >
                                    <textarea
                                      autoFocus
                                      value={
                                        editDraft
                                      }
                                      onChange={(
                                        event
                                      ) =>
                                        setEditDraft(
                                          event
                                            .target
                                            .value
                                        )
                                      }
                                      onKeyDown={(
                                        event
                                      ) => {
                                        if (
                                          event.key
                                            === "Escape"
                                        ) {
                                          cancelMessageEdit();
                                        }

                                        if (
                                          event.key
                                            === "Enter"
                                          && (
                                            event
                                              .metaKey
                                            ||
                                            event
                                              .ctrlKey
                                          )
                                        ) {
                                          event
                                            .preventDefault();

                                          void submitMessageEdit();
                                        }
                                      }}
                                      rows={4}
                                      disabled={
                                        editingMessageSending
                                      }
                                      className="
                                        min-h-[96px]
                                        w-full resize-y
                                        bg-transparent
                                        px-2 py-1
                                        text-[13px]
                                        leading-6
                                        text-[#413438]
                                        outline-none
                                        dark:text-[#eee4e7]
                                      "
                                    />

                                    <p
                                      className="
                                        px-2 pb-2
                                        text-[9px]
                                        leading-4
                                        text-[#9b8e93]
                                        dark:text-[#776b70]
                                      "
                                    >
                                      Bu noktadan
                                      sonraki cevaplar
                                      yeni mesaja göre
                                      yeniden oluşturulur.
                                    </p>

                                    <div
                                      className="
                                        flex
                                        justify-end
                                        gap-2 px-1
                                      "
                                    >
                                      <button
                                        type="button"
                                        onClick={
                                          cancelMessageEdit
                                        }
                                        disabled={
                                          editingMessageSending
                                        }
                                        className="
                                          rounded-lg
                                          px-3 py-1.5
                                          text-[10px]
                                          font-medium
                                          text-[#74666b]
                                          hover:bg-[#eee9e6]
                                          disabled:opacity-40
                                          dark:text-[#a99ca1]
                                          dark:hover:bg-white/[0.05]
                                        "
                                      >
                                        İptal
                                      </button>

                                      <button
                                        type="button"
                                        onClick={() =>
                                          void submitMessageEdit()
                                        }
                                        disabled={
                                          !editDraft
                                            .trim()
                                          ||
                                          editingMessageSending
                                        }
                                        className="
                                          flex
                                          items-center
                                          gap-1.5
                                          rounded-lg
                                          bg-[#35292e]
                                          px-3 py-1.5
                                          text-[10px]
                                          font-medium
                                          text-white
                                          disabled:opacity-40
                                          dark:bg-[#eee2de]
                                          dark:text-[#2b1e23]
                                        "
                                      >
                                        {editingMessageSending
                                          ? (
                                            <Loader2
                                              size={11}
                                              className="animate-spin"
                                            />
                                          )
                                          : (
                                            <Check
                                              size={11}
                                            />
                                          )}

                                        Kaydet ve
                                        yeniden oluştur
                                      </button>
                                    </div>
                                  </div>
                                ) : (
                                  <>
                                    <div
                                      className="
                                        ml-auto
                                        w-fit
                                        max-w-full
                                        rounded-[18px]
                                        rounded-br-md
                                        bg-[#f0ece9]
                                        px-4 py-2.5
                                        text-[13px]
                                        leading-6
                                        text-[#413438]
                                        dark:bg-white/[0.09]
                                        dark:text-[#eee4e7]
                                      "
                                    >
                                      <p
                                        className="
                                          whitespace-pre-wrap
                                        "
                                      >
                                        {
                                          message.content
                                        }
                                      </p>
                                    </div>

                                    <div
                                      className="
                                        mt-1 flex
                                        justify-end
                                        opacity-0
                                        transition-opacity
                                        group-hover:opacity-100
                                      "
                                    >
                                      <button
                                        type="button"
                                        onClick={() =>
                                          beginMessageEdit(
                                            message
                                          )
                                        }
                                        disabled={
                                          sending
                                          ||
                                          regenerating
                                          ||
                                          editingMessageSending
                                        }
                                        className="
                                          flex h-7
                                          items-center
                                          gap-1.5
                                          rounded-md
                                          px-2
                                          text-[10px]
                                          text-[#988b90]
                                          hover:bg-[#f4f0ee]
                                          hover:text-[#5e5055]
                                          disabled:opacity-40
                                          dark:text-[#71656b]
                                          dark:hover:bg-white/[0.05]
                                          dark:hover:text-[#b5a8ad]
                                        "
                                      >
                                        <Pencil
                                          size={11}
                                        />

                                        Düzenle
                                      </button>
                                    </div>
                                  </>
                                )}
                              </div>

                              <div
                                className="
                                  mt-1 flex h-7
                                  w-7 shrink-0
                                  items-center
                                  justify-center
                                  rounded-full
                                  bg-[#352a2e]
                                  text-white
                                  dark:bg-[#ece0dc]
                                  dark:text-[#2a1d22]
                                "
                              >
                                <UserRound
                                  size={13}
                                />
                              </div>
                            </div>
                          </div>
                        );
                      }

                      return (
                        <div
                          key={message.id}
                          className="
                            group flex
                            items-start gap-3
                          "
                        >
                          <div
                            className="
                              mt-0.5 flex h-7
                              w-7 shrink-0
                              items-center
                              justify-center
                              rounded-full
                              border
                              border-[#eaded9]
                              bg-[#faf7f5]
                              text-[#bd5834]
                              dark:border-white/[0.08]
                              dark:bg-white/[0.04]
                              dark:text-[#ff9870]
                            "
                          >
                            <Bot
                              size={14}
                              strokeWidth={1.8}
                            />
                          </div>

                          <div className="min-w-0 flex-1">
                            <MarkdownContent
                              content={
                                message.content
                              }
                            />

                            {messageToolCalls.length > 0 && (
                              <details
                                className="
                                  group/tools mt-4
                                  rounded-xl
                                  border
                                  border-[#e8e0dd]
                                  bg-[#faf8f7]
                                  dark:border-white/[0.07]
                                  dark:bg-white/[0.025]
                                "
                              >
                                <summary
                                  className="
                                    flex cursor-pointer
                                    list-none items-center
                                    justify-between gap-3
                                    px-3 py-2.5
                                    text-[10px]
                                    font-medium
                                    text-[#786a6f]
                                    marker:content-none
                                    dark:text-[#93868c]
                                  "
                                >
                                  <span
                                    className="
                                      flex items-center
                                      gap-2
                                    "
                                  >
                                    <Wrench
                                      size={12}
                                    />

                                    {messageToolCalls.length}
                                    {" "}
                                    araç kullanıldı
                                  </span>

                                  <ChevronDown
                                    size={13}
                                    className="
                                      transition-transform
                                      group-open/tools:rotate-180
                                    "
                                  />
                                </summary>

                                <div
                                  className="
                                    border-t
                                    border-[#ece5e2]
                                    px-3 py-2
                                    dark:border-white/[0.06]
                                  "
                                >
                                  <div
                                    className="
                                      space-y-1
                                    "
                                  >
                                    {messageToolCalls.map(
                                      (
                                        toolCall,
                                        index
                                      ) => {
                                        const failed =
                                          toolCall.status
                                            === "error"
                                          ||
                                          toolCall.status
                                            === "failed";

                                        return (
                                          <div
                                            key={
                                              toolCall.id
                                              ??
                                              `${toolCall.name}-${index}`
                                            }
                                            className="
                                              flex items-center
                                              justify-between
                                              gap-3
                                              rounded-lg
                                              px-2 py-1.5
                                              text-[10px]
                                            "
                                          >
                                            <span
                                              className="
                                                flex min-w-0
                                                items-center
                                                gap-2
                                                text-[#62555a]
                                                dark:text-[#aaa0a4]
                                              "
                                            >
                                              {failed ? (
                                                <CircleX
                                                  size={12}
                                                  className="
                                                    shrink-0
                                                    text-red-500
                                                  "
                                                />
                                              ) : (
                                                <CircleCheck
                                                  size={12}
                                                  className="
                                                    shrink-0
                                                    text-[#708b73]
                                                    dark:text-[#87a98b]
                                                  "
                                                />
                                              )}

                                              <span
                                                className="
                                                  truncate
                                                "
                                              >
                                                {toolDisplayName(
                                                  toolCall.name
                                                )}
                                              </span>
                                            </span>

                                            <span
                                              className="
                                                shrink-0
                                                text-[9px]
                                                text-[#a09498]
                                                dark:text-[#675c61]
                                              "
                                            >
                                              {failed
                                                ? "Hata"
                                                : toolCall.status
                                                  === "success"
                                                  ? "Tamamlandı"
                                                  : "Çalıştırıldı"}
                                            </span>
                                          </div>
                                        );
                                      }
                                    )}
                                  </div>
                                </div>
                              </details>
                            )}

                            <div
                              className="
                                mt-3 flex
                                items-center gap-1
                                opacity-0
                                transition-opacity
                                group-hover:opacity-100
                              "
                            >
                              {message.id ===
                                conversation
                                  ?.messages[
                                    conversation
                                      .messages
                                      .length - 1
                                  ]?.id && (
                                <button
                                  type="button"
                                  onClick={() =>
                                    void handleRegenerate()
                                  }
                                  disabled={
                                    sending ||
                                    regenerating
                                  }
                                  className="
                                    flex h-7
                                    items-center gap-1.5
                                    rounded-md
                                    px-2
                                    text-[10px]
                                    text-[#988b90]
                                    transition
                                    hover:bg-[#f4f0ee]
                                    hover:text-[#5e5055]
                                    disabled:opacity-40
                                    dark:text-[#71656b]
                                    dark:hover:bg-white/[0.05]
                                    dark:hover:text-[#b5a8ad]
                                  "
                                  title="Yanıtı yeniden oluştur"
                                >
                                  <RotateCcw
                                    size={12}
                                    className={
                                      regenerating
                                        ? "animate-spin"
                                        : ""
                                    }
                                  />

                                  {regenerating
                                    ? "Yeniden oluşturuluyor"
                                    : "Yeniden oluştur"}
                                </button>
                              )}

                              <button
                                type="button"
                                onClick={() =>
                                  void handleCopy(
                                    message.id,
                                    message.content
                                  )
                                }
                                className="
                                  flex h-7
                                  items-center gap-1.5
                                  rounded-md
                                  px-2
                                  text-[10px]
                                  text-[#988b90]
                                  transition
                                  hover:bg-[#f4f0ee]
                                  hover:text-[#5e5055]
                                  dark:text-[#71656b]
                                  dark:hover:bg-white/[0.05]
                                  dark:hover:text-[#b5a8ad]
                                "
                              >
                                {copiedMessageId
                                  === message.id
                                  ? (
                                    <Check
                                      size={12}
                                    />
                                  )
                                  : (
                                    <Copy
                                      size={12}
                                    />
                                  )}

                                {copiedMessageId
                                  === message.id
                                  ? "Kopyalandı"
                                  : "Kopyala"}
                              </button>

                              {message.model && (
                                <span
                                  className="
                                    px-2 text-[9px]
                                    text-[#aaa0a3]
                                    dark:text-[#655a60]
                                  "
                                >
                                  {
                                    providerDisplayName(
                                      message.provider
                                    )
                                  }
                                  {" · "}
                                  {message.model}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    }
                  )}

                  {sending && (
                    <div
                      className="
                        flex items-start gap-3
                      "
                    >
                      <div
                        className="
                          mt-0.5 flex h-7
                          w-7 shrink-0
                          items-center
                          justify-center
                          rounded-full
                          border
                          border-[#eaded9]
                          bg-[#faf7f5]
                          text-[#bd5834]
                          dark:border-white/[0.08]
                          dark:bg-white/[0.04]
                          dark:text-[#ff9870]
                        "
                      >
                        <Bot
                          size={14}
                        />
                      </div>

                      <div className="min-w-0 flex-1">
                        {toolStatus && (
                          <div
                            className="
                              mb-3 flex
                              items-center gap-2
                              text-[11px]
                              font-medium
                              text-[#a9674d]
                              dark:text-[#d98c6c]
                            "
                          >
                            <Loader2
                              size={13}
                              className="animate-spin"
                            />

                            {toolStatus}
                          </div>
                        )}

                        {streamingText ? (
                          <MarkdownContent
                            content={
                              streamingText
                            }
                            streaming
                          />
                        ) : (
                          <div
                            className="
                              flex items-center
                              gap-2 text-xs
                              text-[#918489]
                              dark:text-[#81747a]
                            "
                          >
                            {!toolStatus && (
                              <>
                                <Loader2
                                  size={13}
                                  className="animate-spin"
                                />

                                Düşünüyor
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div
                    ref={
                      messagesEndRef
                    }
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {!isAtBottom && (
          <button
            type="button"
            onClick={() =>
              scrollToLatest(
                "smooth"
              )
            }
            className="
              absolute
              bottom-[112px]
              left-1/2 z-20
              flex -translate-x-1/2
              items-center gap-2
              rounded-full
              border
              border-[#ded5d1]
              bg-white
              px-3 py-2
              text-[10px]
              font-medium
              text-[#65585d]
              shadow-[0_8px_28px_rgba(45,31,37,0.14)]
              transition
              hover:bg-[#f8f5f3]
              dark:border-white/[0.10]
              dark:bg-[#241a21]
              dark:text-[#c9bcc1]
              dark:shadow-[0_10px_30px_rgba(0,0,0,0.28)]
              dark:hover:bg-[#2c2028]
            "
            title="En yeni mesaja git"
          >
            <ChevronDown
              size={13}
            />

            {newResponseAvailable
              ? "Yeni yanıt"
              : "Aşağı in"}
          </button>
        )}

        <footer
          className="
            shrink-0
            bg-gradient-to-t
            from-white
            via-white
            to-white/80
            px-4 pb-4 pt-2
            sm:px-6
            dark:from-[#171016]
            dark:via-[#171016]
            dark:to-[#171016]/80
          "
        >
          <div
            className="
              mx-auto w-full
              max-w-[860px]
            "
          >
            {error && (
              <div
                className="
                  mb-2 rounded-lg
                  border border-red-200
                  bg-red-50
                  px-3 py-2
                  text-[11px]
                  text-red-700
                  dark:border-red-400/15
                  dark:bg-red-400/[0.07]
                  dark:text-red-300
                "
              >
                {error}
              </div>
            )}

            <div
              className="
                rounded-[22px]
                border
                border-[#ded5d1]
                bg-white
                p-2
                shadow-[0_10px_35px_rgba(42,29,35,0.09)]
                transition
                focus-within:border-[#cdb9af]
                dark:border-white/[0.10]
                dark:bg-[#21171e]
                dark:shadow-[0_14px_40px_rgba(0,0,0,0.18)]
                dark:focus-within:border-white/[0.17]
              "
            >
              <textarea
                ref={textareaRef}
                value={draft}
                onChange={(event) =>
                  setDraft(
                    event.target.value
                  )
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter"
                    && !event.shiftKey
                    && !event.nativeEvent
                      .isComposing
                  ) {
                    event.preventDefault();

                    void handleSend();
                  }
                }}
                rows={1}
                disabled={sending}
                placeholder="VERITAS'a mesaj gönder..."
                className="
                  max-h-[180px]
                  min-h-[44px]
                  w-full resize-none
                  overflow-y-auto
                  bg-transparent
                  px-3 pb-1 pt-2.5
                  text-[14px]
                  leading-6
                  text-[#3e3236]
                  outline-none
                  placeholder:text-[#aaa0a3]
                  disabled:opacity-70
                  dark:text-[#eee4e7]
                  dark:placeholder:text-[#6f6268]
                "
              />

              <div
                className="
                  mt-1 flex
                  items-center
                  justify-between
                  gap-3 px-1
                "
              >
                <div
                  className="
                    flex min-w-0
                    items-center gap-2
                  "
                >
                  <span
                    className="
                      truncate rounded-md
                      bg-[#f5f1ef]
                      px-2 py-1
                      text-[9px]
                      font-medium
                      text-[#897b80]
                      dark:bg-white/[0.05]
                      dark:text-[#7d7076]
                    "
                  >
                    {providerDisplayName(
                      selectedProvider
                    )}

                    {activeProvider?.model
                      ? (
                        <>
                          {" · "}
                          {
                            activeProvider
                              .model
                          }
                        </>
                      )
                      : null}
                  </span>

                  {(conversation?.analysis
                    || analysisId) && (
                    <span
                      className="
                        hidden truncate
                        rounded-md
                        bg-[#f5f1ef]
                        px-2 py-1
                        text-[9px]
                        text-[#897b80]
                        sm:inline
                        dark:bg-white/[0.05]
                        dark:text-[#7d7076]
                      "
                    >
                      Analysis #
                      {conversation?.analysis
                        ?? analysisId}
                    </span>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => {
                    if (sending) {
                      handleStop();
                      return;
                    }

                    void handleSend();
                  }}
                  disabled={
                    !sending
                    && !draft.trim()
                  }
                  title={
                    sending
                      ? "Yanıtı durdur"
                      : "Gönder"
                  }
                  className="
                    flex h-9 w-9
                    shrink-0
                    items-center
                    justify-center
                    rounded-full
                    bg-[#35292e]
                    text-white
                    transition
                    hover:bg-[#221a1e]
                    disabled:cursor-not-allowed
                    disabled:bg-[#ded7d4]
                    disabled:text-[#a89da0]
                    dark:bg-[#f0e4df]
                    dark:text-[#2a1c21]
                    dark:hover:bg-white
                    dark:disabled:bg-white/[0.08]
                    dark:disabled:text-[#62565c]
                  "
                >
                  {sending ? (
                    <Square
                      size={13}
                      fill="currentColor"
                    />
                  ) : (
                    <Send
                      size={15}
                    />
                  )}
                </button>
              </div>
            </div>

            <p
              className="
                mt-2 text-center
                text-[9px]
                text-[#aaa0a3]
                dark:text-[#5e5358]
              "
            >
              VERITAS hata yapabilir.
              Model sinyallerini ve kanıtları
              birlikte değerlendirin.
            </p>
          </div>
        </footer>
      </section>
    </div>
  );
}
