<script lang="ts">
    import { onMount } from "svelte";
    import { fetchAuthSession } from "aws-amplify/auth";
    import MessageBubble from "./MessageBubble.svelte";
    import InputArea from "./InputArea.svelte";
    import ThemeToggle from "../ThemeToggle.svelte";
    import { appState } from "$lib/state.svelte";

    // Check if we need to proxy manually or if vite proxies
    const API_BASE = ""; // Relative path because we will proxy

    let messages = $state<any[]>([]);
    let isLoading = $state(false);
    let suggestions = $state<string[]>([]);
    let messagesContainer: HTMLDivElement;

    onMount(() => {
        loadMessages();
        loadSuggestions();
    });

    $effect(() => {
        if (appState.isAuthenticated) {
            console.log("User authenticated, reloading messages...");
            messages = [];
            loadMessages();
            loadSuggestions();
        } else {
            // User logged out - clear messages
            messages = [];
            suggestions = [];
        }
    });

    async function getAuthHeader(): Promise<HeadersInit> {
        try {
            const session = await fetchAuthSession();
            const token = session.tokens?.idToken?.toString();
            return token ? { Authorization: token } : {};
        } catch (e) {
            console.error("Error fetching auth session", e);
            return {};
        }
    }

    async function loadMessages() {
        try {
            const headers = await getAuthHeader();
            const res = await fetch(`${API_BASE}/api/chat`, { headers });
            if (res.ok) {
                const data = await res.json();
                if (data.messages) {
                    messages = data.messages
                        .map((m: any) => ({
                            role: m.role,
                            content: m.content?.[0]?.text || "",
                        }))
                        .filter((m: any) => m.content);
                    scrollToBottom();
                }
            }
        } catch (e) {
            console.error("Failed to load messages", e);
        }
    }

    async function loadSuggestions() {
        try {
            const headers = await getAuthHeader();
            const res = await fetch(`${API_BASE}/api/suggestions`, { headers });
            if (res.ok) {
                const data = await res.json();
                suggestions = data.suggestions || [];
            }
        } catch (e) {
            console.error("Failed to load suggestions", e);
        }
    }

    async function handleSend(text: string) {
        if (!text.trim() || isLoading) return;

        // Optimistic update
        const userMsg = { role: "user", content: text };
        messages = [...messages, userMsg];
        isLoading = true;
        scrollToBottom();

        try {
            const headers = {
                "Content-Type": "application/json",
                ...(await getAuthHeader()),
            };

            const response = await fetch(`${API_BASE}/api/chat`, {
                method: "POST",
                headers,
                body: JSON.stringify({ prompt: text }),
            });

            if (!response.ok) throw new Error("Network error");

            const reader = response.body?.getReader();
            if (!reader) throw new Error("No reader");

            let assistantContent = "";
            let doneStream = false;

            const decoder = new TextDecoder();
            while (!doneStream) {
                const { done, value } = await reader.read();
                if (done) {
                    doneStream = true;
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const dataStr = line.slice(6).trim();
                        if (dataStr === "[DONE]" || dataStr === "") continue;

                        try {
                            let textChunk = "";
                            try {
                                textChunk = JSON.parse(dataStr);
                            } catch {
                                textChunk = dataStr;
                            }

                            assistantContent += textChunk;

                            const lastMsg = messages[messages.length - 1];
                            if (lastMsg && lastMsg.role === "assistant") {
                                messages[messages.length - 1] = {
                                    ...lastMsg,
                                    content: assistantContent,
                                };
                            } else {
                                messages = [
                                    ...messages,
                                    {
                                        role: "assistant",
                                        content: assistantContent,
                                    },
                                ];
                            }
                            scrollToBottom();
                        } catch (e) {
                            console.warn("Parse error", e);
                        }
                    }
                }
            }

            // Reload suggestions after chat
            loadSuggestions();
        } catch (e) {
            console.error(e);
            messages = [
                ...messages,
                {
                    role: "assistant",
                    content:
                        "Sorry, checking property data failed. Please try again.",
                },
            ];
        } finally {
            isLoading = false;
            scrollToBottom();
        }
    }

    async function handleSignOut() {
        try {
            const { signOutUser } = await import("$lib/auth");
            await signOutUser();
            appState.setAuthenticated(false);
            messages = [];
            suggestions = [];
        } catch (e) {
            console.error("Sign out failed", e);
        }
    }

    function scrollToBottom() {
        setTimeout(() => {
            if (messagesContainer) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }, 10);
    }
</script>

<div
    class="flex flex-col h-[70vh] min-h-[500px] max-h-[700px] bg-white dark:bg-[#252525] rounded-xl shadow-[0_20px_40px_var(--shadow-color)] border-2 border-[var(--color-border-primary)] overflow-hidden transition-all duration-300"
>
    <div
        class="bg-gradient-to-r from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] p-5 text-center relative flex justify-between items-center"
    >
        <!-- Theme toggle -->
        <div class="w-8 flex items-center justify-center">
            <ThemeToggle />
        </div>
        <div>
            <h1 class="text-2xl font-bold text-white m-0">
                Chat with Digital Twin
            </h1>
            <p class="mt-1 text-white text-sm font-medium opacity-90">
                Your virtual realtor at your service!!
            </p>
        </div>
        <button
            class="text-white text-sm font-semibold hover:bg-white/20 transition-colors p-2 rounded-lg border border-white/30"
            onclick={() => {
                if (appState.isAuthenticated) {
                    handleSignOut();
                } else {
                    appState.isLoginModalOpen = true;
                }
            }}
        >
            {appState.isAuthenticated ? "Sign Out" : "Login"}
        </button>
    </div>

    <div
        bind:this={messagesContainer}
        class="flex-1 p-5 overflow-y-auto bg-white dark:bg-[#252525] transition-colors duration-300"
    >
        {#each messages as msg}
            <MessageBubble {msg} />
        {/each}

        {#if isLoading && (!messages.length || messages[messages.length - 1].role === "user")}
            <div
                class="flex items-center gap-2 p-3 px-4 mb-4 rounded-[18px] rounded-bl-md border-2 border-[var(--color-border-primary)] bg-gradient-to-br from-[var(--color-msg-assistant-start)] to-[var(--color-msg-assistant-end)] text-[var(--text-primary)] max-w-fit"
            >
                <div class="flex gap-1">
                    <span
                        class="w-1.5 h-1.5 bg-[var(--typing-dot)] rounded-full animate-bounce"
                    ></span>
                    <span
                        class="w-1.5 h-1.5 bg-[var(--typing-dot)] rounded-full animate-bounce [animation-delay:0.2s]"
                    ></span>
                    <span
                        class="w-1.5 h-1.5 bg-[var(--typing-dot)] rounded-full animate-bounce [animation-delay:0.4s]"
                    ></span>
                </div>
                <span class="text-xs opacity-70">Thinking...</span>
            </div>
        {/if}
    </div>

    <!-- Question Suggestions Area -->
    {#if suggestions.length > 0 && !isLoading}
        <div
            class="p-4 bg-[var(--bg-suggestions)] border-t-2 border-[var(--color-border-primary)]"
        >
            <p class="text-sm font-semibold text-[var(--text-primary)] mb-3">
                Suggested questions:
            </p>
            <div class="grid grid-cols-2 gap-2">
                {#each suggestions as suggestion}
                    <button
                        onclick={() => handleSend(suggestion)}
                        class="text-left text-sm p-3 rounded-lg border-2 border-[var(--color-border-primary)] bg-white dark:bg-[var(--bg-container)] hover:bg-gradient-to-br hover:from-[var(--color-msg-user-start)] hover:to-[var(--color-msg-user-end)] hover:border-[var(--color-accent-primary)] transition-all text-[var(--text-primary)] font-medium"
                    >
                        {suggestion}
                    </button>
                {/each}
            </div>
        </div>
    {/if}

    <InputArea onSend={handleSend} disabled={isLoading} />
</div>
