<script lang="ts">
    import { onMount } from "svelte";
    import { fetchAuthSession } from "aws-amplify/auth";
    import { appState } from "$lib/state.svelte";
    import { marked } from "marked";

    // Configure marked for better rendering
    marked.setOptions({
        breaks: true,
        gfm: true,
    });

    const API_BASE = "";

    let messages = $state<any[]>([]);
    let isLoading = $state(false);
    let suggestions = $state<string[]>([]);
    let messagesContainer: HTMLDivElement;
    let inputText = $state("");
    let hasStartedChat = $state(false);
    let textareaRef: HTMLTextAreaElement;

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

    async function handleClearChat() {
        messages = [];
        hasStartedChat = false;
        inputText = "";
        autoResizeTextarea();
    }

    async function handleSend(text: string) {
        if (!text.trim() || isLoading) return;

        hasStartedChat = true;

        const userMsg = { role: "user", content: text };
        messages = [...messages, userMsg];
        isLoading = true;
        inputText = "";
        autoResizeTextarea();
        scrollToBottom();

        try {
            const headers = {
                "Content-Type": "application/json",
                ...(await getAuthHeader()),
            };

            console.log("Sending chat request to /api/chat");
            const response = await fetch(`${API_BASE}/api/chat`, {
                method: "POST",
                headers,
                body: JSON.stringify({ prompt: text }),
            });

            console.log("Response status:", response.status, "Headers:", response.headers.get("content-type"));
            if (!response.ok) throw new Error("Failed to send message");

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error("No reader available from response body");
            }

            const decoder = new TextDecoder();
            let buffer = "";
            // Add an empty assistant message that will be updated as chunks arrive
            messages = [...messages, { role: "assistant", content: "" }];
            console.log("Starting to read stream...");

            while (true) {
                const { done, value } = await reader.read();
                console.log("Stream chunk received - done:", done, "bytes:", value?.length);

                if (done) {
                    console.log("Stream complete");
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    console.log("Processing line:", line);
                    if (line.startsWith("data: ")) {
                        const data = line.slice(6).trim();
                        if (data === "[DONE]" || data === "") continue;
                        try {
                            // Backend sends JSON-stringified text, e.g., "Hello" -> becomes the string Hello
                            // It could be a plain string or an object with {text: "..."}
                            const parsed = JSON.parse(data);
                            console.log("Parsed data:", parsed, "type:", typeof parsed);
                            let textChunk = "";

                            if (typeof parsed === "string") {
                                // Backend sends: data: "chunk text"\n\n
                                textChunk = parsed;
                            } else if (
                                parsed &&
                                typeof parsed.text === "string"
                            ) {
                                // Alternative format: data: {"text": "chunk"}\n\n
                                textChunk = parsed.text;
                            } else if (parsed && typeof parsed === "object") {
                                // Handle error objects
                                if (parsed.error) {
                                    console.error(
                                        "Stream error:",
                                        parsed.error,
                                    );
                                    continue;
                                }
                            }

                            if (textChunk) {
                                console.log("Adding text chunk:", textChunk);
                                // Update the assistant message content
                                const lastIndex = messages.length - 1;
                                const updatedContent =
                                    messages[lastIndex].content + textChunk;
                                // Create a new object to trigger Svelte 5 reactivity
                                messages[lastIndex] = {
                                    ...messages[lastIndex],
                                    content: updatedContent,
                                };
                                // Force reactivity by reassigning the array
                                messages = messages;
                                scrollToBottom();
                            }
                        } catch (parseError) {
                            // If JSON parsing fails, try using the raw data as text
                            console.warn(
                                "Parse warning:",
                                parseError,
                                "Raw data:",
                                data,
                            );
                        }
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

    function renderMarkdown(text: string): string {
        try {
            return marked.parse(text) as string;
        } catch (e) {
            console.error("Markdown parsing error:", e);
            return text.replace(/\n/g, "<br/>");
        }
    }

    function autoResizeTextarea() {
        if (textareaRef) {
            textareaRef.style.height = "auto";
            textareaRef.style.height =
                Math.min(textareaRef.scrollHeight, 200) + "px";
        }
    }
</script>

<div class="h-full flex flex-col bg-[var(--bg-body)]">
    <!-- Clear Chat Button - Fixed top right -->
    {#if messages.length > 0}
        <div class="border-b border-[var(--border-light)] bg-[var(--bg-body)]">
            <div class="max-w-[48rem] mx-auto px-3 py-2 sm:px-4 flex justify-end">
                <button
                    onclick={handleClearChat}
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--text-secondary)] hover:bg-white transition-colors"
                >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                    <span>Clear chat</span>
                </button>
            </div>
        </div>
    {/if}

    <!-- Messages Area -->
    <div class="flex-1 overflow-y-auto" bind:this={messagesContainer}>
        <div class="max-w-[48rem] mx-auto px-3 py-4 sm:px-4 sm:py-6">
            {#if messages.length === 0 && !hasStartedChat}
                <!-- Welcome State -->
                <div
                    class="flex flex-col items-center justify-center min-h-[50vh]"
                >
                    <div class="mb-4">
                        <div class="w-10 h-10 rounded-lg bg-black flex items-center justify-center">
                            <svg
                                class="w-6 h-6 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                                />
                            </svg>
                        </div>
                    </div>
                    <h1
                        class="text-xl sm:text-2xl font-semibold text-[var(--text-primary)] mb-1"
                    >
                        Virtual Realtor
                    </h1>
                    <p
                        class="text-sm text-[var(--text-secondary)] text-center max-w-sm px-4"
                    >
                        Ask about properties, neighborhoods, or your home search
                    </p>
                </div>
            {:else}
                <!-- Messages -->
                {#each messages as message, index}
                    <div class="mb-4 animate-fade-in">
                        {#if message.role === "user"}
                            <!-- User Message - Right aligned, light gray pill -->
                            <div class="flex justify-end">
                                <div
                                    class="max-w-[85%] bg-[var(--color-msg-user)] rounded-2xl px-4 py-2.5"
                                >
                                    <p
                                        class="text-[var(--color-msg-user-text)] text-sm whitespace-pre-wrap leading-relaxed"
                                    >
                                        {message.content}
                                    </p>
                                </div>
                            </div>
                        {:else}
                            <!-- Assistant Message - Left aligned, no background -->
                            <div class="max-w-full">
                                <div
                                    class="markdown-content text-[var(--text-primary)] text-sm"
                                >
                                    {@html renderMarkdown(message.content)}
                                </div>
                            </div>
                        {/if}
                    </div>
                {/each}

                {#if isLoading}
                    <div class="mb-6 animate-fade-in">
                        <div class="flex items-center gap-1">
                            <span
                                class="typing-dot w-2 h-2 bg-[var(--text-muted)] rounded-full"
                            ></span>
                            <span
                                class="typing-dot w-2 h-2 bg-[var(--text-muted)] rounded-full"
                            ></span>
                            <span
                                class="typing-dot w-2 h-2 bg-[var(--text-muted)] rounded-full"
                            ></span>
                        </div>
                    </div>
                {/if}
            {/if}
        </div>
    </div>

    <!-- Input Area - Fixed at bottom -->
    <div class="border-t border-[var(--border-light)] bg-[var(--bg-body)]">
        <div class="max-w-[48rem] mx-auto px-3 py-3 sm:px-4 sm:py-4">
            <!-- Question Suggestions -->
            {#if suggestions.length > 0 && messages.length === 0 && !hasStartedChat}
                <div class="mb-3 flex flex-wrap gap-2">
                    {#each suggestions as suggestion}
                        <button
                            onclick={() => handleSend(suggestion)}
                            class="px-3 py-1.5 text-xs rounded-lg bg-white border border-[var(--border-light)] text-[var(--text-secondary)] transition-colors"
                        >
                            {suggestion}
                        </button>
                    {/each}
                </div>
            {/if}

            <!-- Input Container -->
            <div
                class="relative bg-white rounded-2xl border border-[var(--border-light)] shadow-sm focus-within:border-black transition-all"
            >
                <div class="flex items-end gap-3 px-4 py-3">
                    <!-- Text Input -->
                    <textarea
                        bind:this={textareaRef}
                        bind:value={inputText}
                        oninput={autoResizeTextarea}
                        onkeydown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                handleSend(inputText);
                            }
                        }}
                        placeholder="Message Virtual Realtor"
                        rows="1"
                        class="flex-1 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none text-base resize-none leading-6 py-1"
                        style="min-height: 24px; max-height: 160px;"
                    ></textarea>

                    <!-- Send Button -->
                    <button
                        aria-label="Send message"
                        onclick={() => handleSend(inputText)}
                        disabled={!inputText.trim() || isLoading}
                        class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all {inputText.trim() &&
                        !isLoading
                            ? 'bg-black text-white hover:bg-gray-800'
                            : 'bg-[var(--border-light)] text-[var(--text-muted)] cursor-not-allowed'}"
                    >
                        <svg
                            class="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M14 5l7 7m0 0l-7 7m7-7H3"
                            />
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Footer Text -->
            <p class="text-center text-xs text-[var(--text-muted)] mt-2">
                Virtual Realtor can make mistakes. Check important info.
            </p>
        </div>
    </div>
</div>
