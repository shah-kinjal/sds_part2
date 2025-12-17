<script lang="ts">
    import { onMount } from "svelte";
    import { fetchAuthSession } from "aws-amplify/auth";
    import { appState } from "$lib/state.svelte";
    import { marked } from 'marked';

    // Configure marked for better rendering
    marked.setOptions({
        breaks: true,        // Convert \n to <br>
        gfm: true,          // GitHub Flavored Markdown
        headerIds: false,    // Don't add IDs to headers
        mangle: false        // Don't escape email addresses
    });

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
                // Scroll to top to show latest messages
                messagesContainer.scrollTop = 0;
            }
        }, 0);
    }

    function renderMarkdown(text: string): string {
        try {
            return marked.parse(text) as string;
        } catch (e) {
            console.error('Markdown parsing error:', e);
            return text.replace(/\n/g, '<br/>');
        }
    }
</script>

<div class="h-full flex flex-col items-center bg-[var(--bg-body)] overflow-hidden">
    <!-- Permanent Header - Always Visible -->
    <div class="w-full bg-white border-b border-[var(--border-light)] flex-shrink-0">
        <div class="w-3/5 mx-auto px-6 py-8 text-center">
            <h1 class="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-3">
                Find Your Dream Home
            </h1>
            <p class="text-base text-[var(--text-secondary)] max-w-2xl mx-auto">
                Chat with your AI real estate assistant to discover properties that match your lifestyle and budget.
            </p>
        </div>
    </div>

    {#if !hasStartedChat && messages.length === 0}
        <!-- Welcome Screen - Centered (60% width) -->
        <div class="flex-1 flex flex-col items-center justify-center px-6 py-12 w-3/5 mx-auto">
            <div class="w-full max-w-2xl animate-fade-in">

                <!-- Main Input Area - Prominent -->
                <div class="relative mt-8">
                    <div class="bg-white rounded-2xl shadow-xl border border-[var(--border-light)] hover:shadow-2xl transition-shadow">
                        <div class="flex items-end gap-3 p-5">
                            <textarea
                                bind:value={inputText}
                                onkeydown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSend(inputText);
                                    }
                                }}
                                placeholder="Tell me what you're looking for..."
                                rows="2"
                                class="flex-1 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none text-base resize-none px-2 py-2"
                                style="min-height: 60px; max-height: 150px;"
                            />
                            <button
                                onclick={() => handleSend(inputText)}
                                disabled={!inputText.trim() || isLoading}
                                class="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg transition-all flex items-center justify-center"
                            >
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    
                    <!-- Quick Starter Buttons -->
                    <div class="mt-6 flex flex-wrap justify-center gap-3">
                        <button
                            onclick={() => handleSend("I'm looking for a 3 bedroom house under $800k")}
                            class="px-4 py-2 rounded-full bg-[var(--bg-container)] text-[var(--text-secondary)] text-sm hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border-light)]"
                        >
                            🏡 Find me a house
                        </button>
                        <button
                            onclick={() => handleSend("What neighborhoods have good schools?")}
                            class="px-4 py-2 rounded-full bg-[var(--bg-container)] text-[var(--text-secondary)] text-sm hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border-light)]"
                        >
                            🎓 Good schools
                        </button>
                        <button
                            onclick={() => handleSend("Show me properties near parks")}
                            class="px-4 py-2 rounded-full bg-[var(--bg-container)] text-[var(--text-secondary)] text-sm hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border-light)]"
                        >
                            🌳 Near parks
                        </button>
                    </div>
                </div>

                <!-- Footer -->
                <p class="text-center text-xs text-[var(--text-muted)] mt-8">
                    Your AI assistant can help you find properties, answer questions, and guide your home search.
                </p>
            </div>
        </div>
    {:else}
        <!-- Conversation View - Centered Container (60% width) -->
        <div class="w-3/5 mx-auto flex flex-col flex-1 overflow-hidden px-6">
            <!-- Messages Area (Latest at top) -->
            <div class="flex-1 overflow-y-auto scroll-smooth py-8" bind:this={messagesContainer}>
                {#each messages.slice().reverse() as message, index}
                    <div class="mb-8 animate-slide-in" style="animation-delay: {index * 0.05}s;">
                        {#if message.role === 'user'}
                            <!-- User Message -->
                            <div class="flex justify-end">
                                <div class="max-w-[80%]">
                                    <div class="bg-[var(--color-msg-user)] text-[var(--color-msg-user-text)] rounded-3xl rounded-tr-lg px-6 py-4 shadow-sm">
                                        <p class="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                                    </div>
                                </div>
                            </div>
                        {:else}
                            <!-- Assistant Message -->
                            <div class="flex gap-4">
                                <div class="flex-shrink-0">
                                    <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center shadow-md">
                                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                                        </svg>
                                    </div>
                                </div>
                                <div class="flex-1 max-w-[80%]">
                                    <div class="bg-[var(--color-msg-assistant)] rounded-3xl rounded-tl-lg px-6 py-4 shadow-sm border border-[var(--border-light)]">
                                        <div class="markdown-content text-[var(--color-msg-assistant-text)]">
                                            {@html renderMarkdown(message.content)}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/if}
                    </div>
                {/each}

                {#if isLoading}
                    <div class="mb-8 flex gap-4 animate-fade-in">
                        <div class="flex-shrink-0">
                            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center shadow-md">
                                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                                </svg>
                            </div>
                        </div>
                        <div class="flex items-center gap-1.5 px-6 py-4">
                            <span class="w-2.5 h-2.5 bg-[var(--color-primary)] rounded-full animate-bounce"></span>
                            <span class="w-2.5 h-2.5 bg-[var(--color-primary)] rounded-full animate-bounce [animation-delay:0.15s]"></span>
                            <span class="w-2.5 h-2.5 bg-[var(--color-primary)] rounded-full animate-bounce [animation-delay:0.3s]"></span>
                        </div>
                    </div>
                {/if}
            </div>

            <!-- Fixed Bottom Input Area -->
            <div class="border-t border-[var(--border-light)] bg-white/80 backdrop-blur-sm py-6 pb-8">
                <!-- Suggestions Pills -->
                {#if suggestions.length > 0}
                    <div class="mb-4 flex flex-wrap gap-2 animate-fade-in">
                        {#each suggestions as suggestion}
                            <button
                                onclick={() => handleSend(suggestion)}
                                class="text-sm px-4 py-2 rounded-full bg-[var(--bg-container)] text-[var(--text-secondary)] border border-[var(--border-light)] hover:bg-[var(--bg-hover)] hover:border-[var(--border-medium)] transition-all"
                            >
                                {suggestion}
                            </button>
                        {/each}
                    </div>
                {/if}

                <!-- Input Box (Larger) -->
                <div class="bg-white rounded-2xl shadow-lg border border-[var(--border-light)] focus-within:border-[var(--color-primary)] focus-within:shadow-xl transition-all mb-4">
                    <div class="flex items-end gap-3 p-5">
                        <textarea
                            bind:value={inputText}
                            onkeydown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend(inputText);
                                }
                            }}
                            placeholder="Ask me anything..."
                            rows="2"
                            class="flex-1 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none text-base resize-none px-2 py-2"
                            style="min-height: 60px; max-height: 150px;"
                        />
                        <button
                            onclick={() => handleSend(inputText)}
                            disabled={!inputText.trim() || isLoading}
                            class="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg transition-all flex items-center justify-center"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Quick Starter Buttons (Always at bottom) -->
                <div class="flex flex-wrap justify-center gap-2 mb-3">
                    <button
                        onclick={() => handleSend("I'm looking for a 3 bedroom house under $800k")}
                        class="px-4 py-2 rounded-full bg-[var(--bg-container)] text-[var(--text-secondary)] text-sm hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border-light)]"
                    >
                        🏡 Find me a house
                    </button>
                    <button
                        onclick={() => handleSend("What neighborhoods have good schools?")}
                        class="px-4 py-2 rounded-full bg-[var(--bg-container)] text-[var(--text-secondary)] text-sm hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border-light)]"
                    >
                        🎓 Good schools
                    </button>
                    <button
                        onclick={() => handleSend("Show me properties near parks")}
                        class="px-4 py-2 rounded-full bg-[var(--bg-container)] text-[var(--text-secondary)] text-sm hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border-light)]"
                    >
                        🌳 Near parks
                    </button>
                </div>

                <!-- Footer (Always at bottom) -->
                <p class="text-center text-xs text-[var(--text-muted)]">
                    Your AI assistant can help you find properties, answer questions, and guide your home search.
                </p>
            </div>
        </div>
    {/if}
</div>
