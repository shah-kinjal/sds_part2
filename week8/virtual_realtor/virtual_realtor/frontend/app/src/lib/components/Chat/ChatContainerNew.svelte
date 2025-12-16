<script lang="ts">
    import { onMount } from "svelte";
    import { fetchAuthSession } from "aws-amplify/auth";
    import { appState } from "$lib/state.svelte";

    const API_BASE = "";

    let messages = $state<any[]>([]);
    let isLoading = $state(false);
    let suggestions = $state<string[]>([]);
    let messagesContainer: HTMLDivElement;
    let inputText = $state("");
    let hasStartedChat = $state(false);

    onMount(() => {
        loadMessages();
        loadSuggestions();
    });

    $effect(() => {
        if (appState.isAuthenticated) {
            messages = [];
            loadMessages();
            loadSuggestions();
        } else {
            messages = [];
            suggestions = [];
            hasStartedChat = false;
        }
    });

    async function getAuthHeader(): Promise<HeadersInit> {
        try {
            const session = await fetchAuthSession();
            const token = session.tokens?.idToken?.toString();
            return token ? { Authorization: token } : {};
        } catch (e) {
            return {};
        }
    }

    async function loadMessages() {
        try {
            const headers = await getAuthHeader();
            const res = await fetch(`${API_BASE}/api/chat`, { headers });
            if (res.ok) {
                const data = await res.json();
                if (data.messages && data.messages.length > 0) {
                    messages = data.messages
                        .map((m: any) => ({
                            role: m.role,
                            content: m.content?.[0]?.text || "",
                        }))
                        .filter((m: any) => m.content);
                    hasStartedChat = true;
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

        hasStartedChat = true;

        const userMsg = { role: "user", content: text };
        messages = [...messages, userMsg];
        isLoading = true;
        inputText = "";
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

            if (!response.ok) throw new Error("Failed to send message");

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let assistantMsg = { role: "assistant", content: "" };
            messages = [...messages, assistantMsg];

            while (reader) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const data = line.slice(6);
                        if (data === "[DONE]") continue;
                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.text) {
                                assistantMsg.content += parsed.text;
                                messages = [...messages];
                                scrollToBottom();
                            }
                        } catch {}
                    }
                }
            }

            loadSuggestions();
        } catch (e) {
            console.error("Error:", e);
            messages = messages.slice(0, -1);
        } finally {
            isLoading = false;
        }
    }

    function scrollToBottom() {
        setTimeout(() => {
            if (messagesContainer) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }, 0);
    }

    function handleSignOut() {
        appState.signOut();
        messages = [];
        suggestions = [];
        hasStartedChat = false;
    }
</script>

<div class="h-full flex flex-col bg-[var(--bg-body)]">
    {#if !hasStartedChat && messages.length === 0}
        <!-- Initial Centered View -->
        <div class="flex-1 flex flex-col items-center justify-center px-4">
            <div class="w-full max-w-2xl">
                <h1 class="text-4xl font-semibold text-center text-[var(--text-primary)] mb-12">
                    What can I help with?
                </h1>

                <!-- Input Area -->
                <div class="relative">
                    <div class="bg-[var(--input-bg)] rounded-3xl shadow-sm border border-[var(--color-border-primary)]">
                        <div class="flex items-center gap-3 px-4 py-3">
                            <input
                                type="text"
                                bind:value={inputText}
                                onkeydown={(e) => e.key === 'Enter' && handleSend(inputText)}
                                placeholder="Message Virtual Realtor"
                                class="flex-1 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none text-base"
                            />
                            <button
                                onclick={() => handleSend(inputText)}
                                disabled={!inputText.trim() || isLoading}
                                class="p-2 rounded-lg bg-[var(--text-primary)] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-80 transition-opacity"
                            >
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Footer Text -->
                <p class="text-center text-xs text-[var(--text-muted)] mt-4">
                    Virtual Realtor can make mistakes. Consider checking important information.
                </p>
            </div>
        </div>
    {:else}
        <!-- Chat View -->
        <div class="flex-1 overflow-y-auto" bind:this={messagesContainer}>
            <div class="max-w-2xl mx-auto px-4 py-8">
                {#each messages as message}
                    <div class="mb-6">
                        <div class="flex gap-4 {message.role === 'user' ? 'justify-end' : ''}">
                            {#if message.role === 'assistant'}
                                <div class="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--color-accent-primary)] flex items-center justify-center text-white font-semibold text-sm">
                                    VR
                                </div>
                            {/if}
                            <div class="flex-1 {message.role === 'user' ? 'flex justify-end' : ''}">
                                <div class="max-w-[85%] {message.role === 'user' ? 'bg-[var(--input-bg)] text-[var(--text-primary)] px-4 py-3 rounded-3xl' : 'text-[var(--text-primary)]'}">
                                    {#if message.role === 'user'}
                                        <div class="whitespace-pre-wrap">{message.content}</div>
                                    {:else}
                                        <div class="prose prose-sm max-w-none">
                                            {@html message.content.replace(/\n/g, '<br/>')}
                                        </div>
                                    {/if}
                                </div>
                            </div>
                            {#if message.role === 'user'}
                                <div class="flex-shrink-0 w-8 h-8 rounded-full bg-gray-400 flex items-center justify-center text-white font-semibold text-sm">
                                    U
                                </div>
                            {/if}
                        </div>
                    </div>
                {/each}

                {#if isLoading}
                    <div class="mb-6 flex gap-4">
                        <div class="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--color-accent-primary)] flex items-center justify-center text-white font-semibold text-sm">
                            VR
                        </div>
                        <div class="flex gap-1 pt-2">
                            <span class="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce"></span>
                            <span class="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce [animation-delay:0.2s]"></span>
                            <span class="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce [animation-delay:0.4s]"></span>
                        </div>
                    </div>
                {/if}
            </div>
        </div>

        <!-- Bottom Input Area -->
        <div class="border-t border-[var(--color-border-primary)]">
            <div class="max-w-2xl mx-auto px-4 py-4">
                <div class="bg-[var(--input-bg)] rounded-3xl border border-[var(--color-border-primary)]">
                    <div class="flex items-center gap-3 px-4 py-3">
                        <input
                            type="text"
                            bind:value={inputText}
                            onkeydown={(e) => e.key === 'Enter' && handleSend(inputText)}
                            placeholder="Message Virtual Realtor"
                            class="flex-1 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none text-base"
                        />
                        <button
                            onclick={() => handleSend(inputText)}
                            disabled={!inputText.trim() || isLoading}
                            class="p-2 rounded-lg bg-[var(--text-primary)] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-80 transition-opacity"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
                            </svg>
                        </button>
                    </div>
                </div>

                {#if suggestions.length > 0 && messages.length > 0}
                    <div class="mt-4 flex flex-wrap gap-2">
                        {#each suggestions as suggestion}
                            <button
                                onclick={() => handleSend(suggestion)}
                                class="text-sm px-3 py-1.5 rounded-full bg-[var(--input-bg)] text-[var(--text-primary)] border border-[var(--color-border-primary)] hover:bg-[var(--bg-container)] transition-colors"
                            >
                                {suggestion}
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
    {/if}
</div>
