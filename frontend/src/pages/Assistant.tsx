import {
  Bot,
  FileSearch,
  MessageSquareText,
  Plus,
  Send,
  Trash2,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";
import {
  useSearchParams,
} from "react-router-dom";

import {
  createAssistantConversation,
  deleteAssistantConversation,
  getAgentProviders,
  getAssistantConversation,
  listAssistantConversations,
  type AgentProvider,
  type AssistantConversation,
  type AssistantConversationSummary,
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
    typeof error === "object" &&
    error !== null &&
    "response" in error
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


function toolStatusText(
  toolCall: AssistantToolCall
): string {
  switch (toolCall.name) {
    case "search_evidence":
      return "Kanıtlar aranıyor...";

    case "get_analysis_result":
      return "Analiz sonucu getiriliyor...";

    default:
      return "VERITAS aracı çalışıyor...";
  }
}


export default function Assistant() {
  const [searchParams] =
    useSearchParams();

  const analysisParam =
    searchParams.get("analysis");

  const analysisId =
    analysisParam &&
    Number.isFinite(
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

  const [draft, setDraft] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [sending, setSending] =
    useState(false);

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

  const [error, setError] =
    useState<string | null>(null);


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


  async function openConversation(
    id: string
  ) {
    setError(null);

    try {
      const data =
        await getAssistantConversation(
          id
        );

      setConversation(data);
      setSelectedProvider(
        data.provider
      );
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError
        )
      );
    }
  }


  function startNewChat() {
    setConversation(null);
    setDraft("");
    setError(null);

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


  async function handleDelete() {
    if (!conversation) {
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


  async function handleSend() {
    const content = draft.trim();

    if (
      !content ||
      sending
    ) {
      return;
    }

    setSending(true);
    setError(null);
    setStreamingText("");
    setToolStatus(
      "Yanıt hazırlanıyor..."
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
              "Yanıt oluşturuluyor..."
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

                const withoutDuplicates =
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
                    ...withoutDuplicates,
                    userMessage,
                    assistantMessage,
                  ],
                };
              }
            );

            setStreamingText("");
            setToolStatus(null);
          },
        }
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
      setError(
        getErrorMessage(
          requestError
        )
      );

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
      setStreamingText("");
      setToolStatus(null);
      setSending(false);
    }
  }


  return (
    <div className="mx-auto flex h-[calc(100vh-124px)] min-h-[620px] w-full max-w-[1600px] overflow-hidden rounded-xl border border-[#e6dedb] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1b1218] dark:shadow-dark-panel">
      <aside className="hidden w-[270px] shrink-0 flex-col border-r border-[#ebe4e1] bg-[#fbf9f7] lg:flex dark:border-white/[0.07] dark:bg-[#160f15]">
        <div className="border-b border-[#ebe4e1] p-3 dark:border-white/[0.07]">
          <button
            type="button"
            onClick={
              startNewChat
            }
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#e1d5d0] bg-white px-3 py-2.5 text-xs font-semibold text-[#514348] transition hover:border-[#cfaa9a] dark:border-white/[0.09] dark:bg-white/[0.035] dark:text-[#ddd0d4]"
          >
            <Plus size={15} />
            Yeni sohbet
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {conversations.length ===
            0 && (
            <p className="px-3 py-5 text-center text-[11px] text-[#9b8f93] dark:text-[#74686e]">
              Henüz sohbet yok.
            </p>
          )}

          {conversations.map(
            (item) => {
              const active =
                conversation?.id ===
                item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() =>
                    openConversation(
                      item.id
                    )
                  }
                  className={[
                    "mb-1 w-full rounded-lg px-3 py-3 text-left transition",
                    active
                      ? "bg-[#fff0e8] dark:bg-[#ff895d]/[0.09]"
                      : "hover:bg-[#f3eeeb] dark:hover:bg-white/[0.04]",
                  ].join(" ")}
                >
                  <p className="truncate text-xs font-semibold text-[#504247] dark:text-[#d8cbd0]">
                    {item.title}
                  </p>

                  <p className="mt-1 text-[10px] text-[#9b8e93] dark:text-[#766970]">
                    {item.provider}
                    {" • "}
                    {item.message_count}
                    {" mesaj"}
                  </p>
                </button>
              );
            }
          )}
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-[70px] items-center justify-between gap-4 border-b border-[#ebe4e1] px-5 dark:border-white/[0.07]">
          <div>
            <div className="flex items-center gap-2">
              <MessageSquareText
                size={17}
                className="text-[#c86038] dark:text-[#ff895d]"
              />

              <h1 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
                VERITAS Assistant
              </h1>
            </div>

            <p className="mt-1 text-[10px] text-[#988b90] dark:text-[#7b6e74]">
              {conversation?.analysis
                ? `Analysis #${conversation.analysis} bağlamı`
                : analysisId
                  ? `Yeni sohbet Analysis #${analysisId} ile bağlanacak`
                  : "Analiz ve evidence sonuçlarını açıklayan AI asistan"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-medium uppercase tracking-[0.12em] text-[#988b90] dark:text-[#84767c]">
              Model
            </span>

            <select
              value={
                providers.length
                  ? selectedProvider
                  : ""
              }
              disabled={
                conversation !== null ||
                loading ||
                providers.length === 0
              }
              onChange={(event) =>
                setSelectedProvider(
                  event.target.value
                )
              }
              className="min-w-[230px] rounded-lg border border-[#ded4d0] bg-white px-3 py-2 text-xs text-[#57494e] outline-none transition focus:border-[#c86038]/60 dark:border-white/[0.1] dark:bg-[#20161d] dark:text-[#d9cdd1]"
            >
              {providers.length === 0 && (
                <option
                  value=""
                  disabled
                >
                  {loading
                    ? "Modeller yükleniyor..."
                    : "Model yüklenemedi"}
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
                    {provider.name}
                    {" — "}
                    {provider.model ||
                      "model belirtilmemiş"}
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
                onClick={
                  handleDelete
                }
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#ead8d5] text-[#aa5b55] transition hover:bg-[#fff1ef] dark:border-red-400/10 dark:text-red-300 dark:hover:bg-red-400/[0.06]"
                title="Sohbeti sil"
              >
                <Trash2
                  size={15}
                />
              </button>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-6 lg:px-8">
          {loading ? (
            <div className="flex h-full items-center justify-center text-xs text-[#9b8e93]">
              Assistant yükleniyor...
            </div>
          ) : (
            <>
              {!conversation ||
              conversation.messages
                .length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-[#f0c9b8] bg-[#fff0e7] text-[#bd5733] dark:border-[#ff895d]/20 dark:bg-[#ff895d]/[0.09] dark:text-[#ff9b74]">
                    <Bot size={22} />
                  </div>

                  <h2 className="mt-4 text-base font-semibold text-[#33272b] dark:text-[#f6edef]">
                    VERITAS'a sorun
                  </h2>

                  <p className="mt-2 max-w-[480px] text-xs leading-5 text-[#897c81] dark:text-[#8c7f85]">
                    Analiz sonuçlarını,
                    evidence kaynaklarını,
                    GNN ve bot sinyallerini
                    açıklayabilir veya
                    sonuçların neden farklı
                    olduğunu anlatabilirim.
                  </p>

                  {analysisId && (
                    <div className="mt-4 flex items-center gap-2 rounded-lg border border-[#eaded9] bg-[#fbf8f6] px-3 py-2 text-[11px] text-[#74666c] dark:border-white/[0.07] dark:bg-white/[0.025] dark:text-[#998b91]">
                      <FileSearch
                        size={14}
                      />
                      Analysis #{analysisId}
                      context olarak kullanılacak
                    </div>
                  )}
                </div>
              ) : (
                <div className="mx-auto max-w-[850px] space-y-5">
                  {conversation.messages.map(
                    (message) => {
                      const isUser =
                        message.role ===
                        "user";

                      return (
                        <div
                          key={
                            message.id
                          }
                          className={[
                            "flex gap-3",
                            isUser
                              ? "justify-end"
                              : "justify-start",
                          ].join(" ")}
                        >
                          {!isUser && (
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#fff0e8] text-[#bd5834] dark:bg-[#ff895d]/[0.09] dark:text-[#ff9870]">
                              <Bot
                                size={16}
                              />
                            </div>
                          )}

                          <div
                            className={[
                              "max-w-[78%] rounded-xl px-4 py-3 text-[13px] leading-6",
                              isUser
                                ? "bg-[#33282c] text-white dark:bg-[#eee3df] dark:text-[#241a1e]"
                                : "border border-[#e9e1de] bg-[#fbf9f8] text-[#514449] dark:border-white/[0.07] dark:bg-white/[0.03] dark:text-[#d7cacf]",
                            ].join(" ")}
                          >
                            <p className="whitespace-pre-wrap">
                              {
                                message.content
                              }
                            </p>

                            {!isUser &&
                              message.model && (
                              <p className="mt-2 text-[9px] text-[#a29599] dark:text-[#74686e]">
                                {
                                  message.provider
                                }
                                {" • "}
                                {
                                  message.model
                                }
                              </p>
                            )}
                          </div>

                          {isUser && (
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#f1ece9] text-[#796b70] dark:bg-white/[0.06] dark:text-[#b6a8ad]">
                              <UserRound
                                size={15}
                              />
                            </div>
                          )}
                        </div>
                      );
                    }
                  )}

                  {sending && (
                    <div className="flex items-start gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#fff0e8] text-[#bd5834] dark:bg-[#ff895d]/[0.09] dark:text-[#ff9870]">
                        <Bot size={16} />
                      </div>

                      <div className="max-w-[78%] rounded-xl border border-[#e9e1de] bg-[#fbf9f8] px-4 py-3 text-[13px] leading-6 text-[#514449] dark:border-white/[0.07] dark:bg-white/[0.03] dark:text-[#d7cacf]">
                        {toolStatus && (
                          <p className="mb-1 text-[10px] font-medium text-[#b26a4d] dark:text-[#e69a78]">
                            {toolStatus}
                          </p>
                        )}

                        {streamingText ? (
                          <p className="whitespace-pre-wrap">
                            {streamingText}
                            <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-[#c86038] align-middle dark:bg-[#ff895d]" />
                          </p>
                        ) : (
                          <p className="text-xs text-[#94878c] dark:text-[#81747a]">
                            {toolStatus ??
                              "Yanıt hazırlanıyor..."}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        <footer className="border-t border-[#ebe4e1] p-4 dark:border-white/[0.07]">
          <div className="mx-auto max-w-[850px]">
            {error && (
              <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[11px] text-red-700 dark:border-red-400/15 dark:bg-red-400/[0.07] dark:text-red-300">
                {error}
              </div>
            )}

            <div className="flex items-end gap-2 rounded-xl border border-[#ded5d1] bg-[#fbfaf9] p-2 shadow-[0_8px_24px_rgba(45,31,37,0.04)] focus-within:border-[#cda897] dark:border-white/[0.09] dark:bg-[#160f15]">
              <textarea
                value={draft}
                onChange={(event) =>
                  setDraft(
                    event.target.value
                  )
                }
                onKeyDown={(event) => {
                  if (
                    event.key ===
                      "Enter" &&
                    !event.shiftKey
                  ) {
                    event.preventDefault();
                    handleSend();
                  }
                }}
                rows={2}
                placeholder="VERITAS'a bir şey sorun..."
                className="max-h-40 min-h-[48px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-[#413438] outline-none placeholder:text-[#aaa0a3] dark:text-[#eee4e7] dark:placeholder:text-[#695d63]"
              />

              <button
                type="button"
                onClick={
                  handleSend
                }
                disabled={
                  !draft.trim() ||
                  sending
                }
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#c86038] text-white transition hover:bg-[#b65331] disabled:cursor-not-allowed disabled:opacity-40 dark:bg-[#ff895d] dark:text-[#2c161e]"
              >
                <Send size={16} />
              </button>
            </div>

            <p className="mt-2 text-center text-[9px] text-[#aaa0a3] dark:text-[#62575c]">
              AI yanıtları evidence ve model
              sinyallerinin açıklanmasına yardımcı
              olur; tek başına doğruluk kanıtı değildir.
            </p>
          </div>
        </footer>
      </section>
    </div>
  );
}
