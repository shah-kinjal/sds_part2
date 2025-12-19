<script lang="ts">
    import { onMount } from "svelte";
    import { fetchAuthSession } from "aws-amplify/auth";
    import { appState } from "$lib/state.svelte";
    import { marked } from 'marked';

    // Configure marked for better rendering
    marked.setOptions({
        breaks: true,
        gfm: true
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

    function renderMarkdown(text: string): string {
        try {
            return marked.parse(text) as string;
        } catch (e) {
            console.error('Markdown parsing error:', e);
            return text.replace(/\n/g, '<br/>');
        }
    }

    function autoResizeTextarea() {
        if (textareaRef) {
            textareaRef.style.height = 'auto';
            textareaRef.style.height = Math.min(textareaRef.scrollHeight, 200) + 'px';
        }
    }
</script>

<div class="h-full flex flex-col bg-white">
    <!-- Messages Area -->
    <div class="flex-1 overflow-y-auto" bind:this={messagesContainer}>
        <div class="max-w-3xl mx-auto px-4 py-6">
            {#if messages.length === 0 && !hasStartedChat}
                <!-- Welcome State -->
                <div class="flex flex-col items-center justify-center min-h-[60vh]">
                    <div class="mb-8">
                        <svg class="w-12 h-12 text-[var(--text-primary)]" viewBox="0 0 41 41" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M37.5324 16.8707C37.9808 15.5241 38.1363 14.0974 37.9886 12.6859C37.8409 11.2744 37.3934 9.91076 36.676 8.68622C35.6126 6.83404 33.9882 5.3676 32.0373 4.4985C30.0864 3.62941 27.9098 3.40259 25.8215 3.85078C24.8796 2.7893 23.7219 1.94125 22.4257 1.36341C21.1295 0.785575 19.7249 0.491269 18.3058 0.500898C16.1708 0.495939 14.0893 1.16164 12.3614 2.40166C10.6335 3.64168 9.34853 5.39132 8.69138 7.39717C7.30349 7.6925 5.99631 8.29025 4.85101 9.15038C3.70571 10.0105 2.74887 11.1128 2.04595 12.3835C1.01008 14.2354 0.550086 16.3514 0.72376 18.4614C0.897434 20.5714 1.69676 22.5759 3.02098 24.2166C2.5753 25.5572 2.42045 26.9772 2.56736 28.3824C2.71427 29.7875 3.15963 31.1449 3.87285 32.365C4.93507 34.2213 6.56081 35.691 8.51379 36.562C10.4668 37.433 12.6462 37.6604 14.7374 37.2106C15.6766 38.2721 16.8319 39.1213 18.1258 39.7003C19.4197 40.2793 20.8226 40.5747 22.2405 40.5658C24.3757 40.5709 26.4576 39.9053 28.1857 38.6651C29.9139 37.425 31.199 35.6751 31.8559 33.6689C33.2438 33.3735 34.551 32.7758 35.6963 31.9156C36.8416 31.0555 37.7984 29.9532 38.5013 28.6824C39.5372 26.8305 39.9972 24.7145 39.8235 22.6045C39.6499 20.4945 38.8505 18.49 37.5264 16.8497L37.5324 16.8707ZM22.2495 38.0658C20.654 38.0681 19.0906 37.6003 17.7519 36.7192C17.8117 36.6814 17.9121 36.6203 17.9776 36.5772L26.1325 31.8544C26.3099 31.7518 26.4568 31.6028 26.5577 31.4232C26.6585 31.2436 26.7095 31.0404 26.7056 30.8347V19.4618L30.129 21.4427C30.1445 21.4516 30.1576 21.464 30.1671 21.479C30.1767 21.494 30.1825 21.5111 30.1841 21.5289V30.9537C30.1793 32.5847 29.5282 34.1473 28.3737 35.3017C27.2193 36.4562 25.6567 37.1073 24.0257 37.1121L22.2495 38.0658ZM6.23887 31.0378C5.43811 29.6871 5.13823 28.1037 5.39295 26.5629C5.45091 26.6038 5.5473 26.6697 5.61878 26.7127L13.7737 31.4355C13.9495 31.5401 14.15 31.5955 14.3541 31.5955C14.5582 31.5955 14.7587 31.5401 14.9345 31.4355L25.0076 25.6128V29.5747C25.0091 29.5928 25.0062 29.6111 24.9992 29.6278C24.9922 29.6446 24.9813 29.6593 24.9675 29.6707L16.7119 34.4534C15.2834 35.2718 13.5984 35.5456 11.9796 35.2223C10.3607 34.899 8.9147 34.0007 7.91187 32.6972L6.23887 31.0378ZM4.30219 13.5218C5.09898 12.1678 6.35091 11.1315 7.83474 10.5902C7.83474 10.6582 7.82967 10.7772 7.82967 10.8622V20.3077C7.82578 20.513 7.87634 20.7157 7.97655 20.8948C8.07676 21.074 8.2233 21.2227 8.40024 21.3249L18.4733 27.1477L15.0499 29.1286C15.0347 29.1394 15.0171 29.1465 14.9985 29.1493C14.98 29.1521 14.9612 29.1504 14.9435 29.1445L6.68794 24.3617C5.26289 23.5404 4.17832 22.2327 3.62865 20.6763C3.07898 19.1199 3.10027 17.4216 3.68879 15.8792L4.30219 13.5218ZM32.8003 19.6781L22.7273 13.8553L26.1507 11.8744C26.1659 11.8636 26.1834 11.8565 26.202 11.8537C26.2205 11.8509 26.2393 11.8526 26.257 11.8584L34.5126 16.6412C35.5944 17.2621 36.4913 18.1556 37.1165 19.2351C37.7417 20.3145 38.0741 21.5421 38.0801 22.7936C38.0861 24.0451 37.7654 25.2759 37.1505 26.361C36.5357 27.4462 35.6474 28.3478 34.5716 28.9782L32.8003 19.6781ZM36.1557 14.4349C36.0978 14.394 36.0014 14.3282 35.9299 14.2851L27.775 9.56237C27.5992 9.45776 27.3987 9.40234 27.1946 9.40234C26.9905 9.40234 26.79 9.45776 26.6142 9.56237L16.5412 15.3851V11.4232C16.5397 11.4051 16.5426 11.3868 16.5496 11.3701C16.5565 11.3533 16.5675 11.3386 16.5813 11.3272L24.8368 6.54447C25.9161 5.92472 27.1434 5.59274 28.3948 5.58296C29.6462 5.57318 30.8784 5.88598 31.9668 6.4891C33.0552 7.09222 33.9614 7.96462 34.6004 9.02161C35.2395 10.0786 35.5894 11.2844 35.6157 12.5202L36.1557 14.4349ZM14.5992 21.5371L11.1757 19.5563C11.1602 19.5473 11.1471 19.535 11.1375 19.52C11.128 19.505 11.1222 19.4879 11.1206 19.4701V10.0453C11.1228 8.79225 11.4483 7.56052 12.0668 6.46717C12.6853 5.37382 13.5761 4.45521 14.6519 3.79928C15.7277 3.14335 16.9523 2.77175 18.2114 2.71863C19.4706 2.66551 20.7219 2.93269 21.8474 3.49498L14.5992 21.5371ZM16.5412 25.6128L13.1178 23.6319V15.6709L16.5412 17.6518V25.6128ZM18.6137 23.4407V15.4798L22.0371 17.4607V25.4217L18.6137 23.4407ZM24.1096 17.4607L27.533 15.4798V23.4407L24.1096 25.4217V17.4607ZM27.533 13.3073L24.1096 15.2882L20.6862 13.3073L24.1096 11.3264L27.533 13.3073ZM14.5992 23.4407L11.1757 21.4598V17.4989L14.5992 19.4798V23.4407ZM29.6055 19.4798L33.029 17.4989V21.4598L29.6055 23.4407V19.4798Z" fill="currentColor"/>
                        </svg>
                    </div>
                    <h1 class="text-2xl font-semibold text-[var(--text-primary)] mb-2">
                        Virtual Realtor
                    </h1>
                    <p class="text-[var(--text-secondary)] text-center max-w-md">
                        Ask me anything about properties, neighborhoods, or your home search.
                    </p>
                </div>
            {:else}
                <!-- Messages -->
                {#each messages as message, index}
                    <div class="mb-6 animate-fade-in">
                        {#if message.role === 'user'}
                            <!-- User Message - Right aligned, gray pill -->
                            <div class="flex justify-end">
                                <div class="max-w-[85%] bg-[var(--color-msg-user)] rounded-3xl px-5 py-3">
                                    <p class="text-[var(--color-msg-user-text)] whitespace-pre-wrap leading-relaxed">
                                        {message.content}
                                    </p>
                                </div>
                            </div>
                        {:else}
                            <!-- Assistant Message - Left aligned, no background -->
                            <div class="max-w-full">
                                <div class="markdown-content text-[var(--text-primary)]">
                                    {@html renderMarkdown(message.content)}
                                </div>
                            </div>
                        {/if}
                    </div>
                {/each}

                {#if isLoading}
                    <div class="mb-6 animate-fade-in">
                        <div class="flex items-center gap-1">
                            <span class="typing-dot w-2 h-2 bg-[var(--text-muted)] rounded-full"></span>
                            <span class="typing-dot w-2 h-2 bg-[var(--text-muted)] rounded-full"></span>
                            <span class="typing-dot w-2 h-2 bg-[var(--text-muted)] rounded-full"></span>
                        </div>
                    </div>
                {/if}
            {/if}
        </div>
    </div>

    <!-- Input Area - Fixed at bottom -->
    <div class="border-t border-[var(--border-light)] bg-white">
        <div class="max-w-3xl mx-auto px-4 py-4">
            <!-- Input Container -->
            <div class="relative bg-[var(--bg-container)] rounded-3xl border border-[var(--border-light)] shadow-sm focus-within:border-[var(--border-medium)] focus-within:shadow-md transition-all">
                <div class="flex items-end gap-2 px-4 py-3">
                    <!-- Plus/Attach Button -->
                    <button aria-label="Attach file" class="flex-shrink-0 p-1.5 rounded-full hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                        </svg>
                    </button>

                    <!-- Text Input -->
                    <textarea
                        bind:this={textareaRef}
                        bind:value={inputText}
                        oninput={autoResizeTextarea}
                        onkeydown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend(inputText);
                            }
                        }}
                        placeholder="Ask anything"
                        rows="1"
                        class="flex-1 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none text-base resize-none leading-6 py-1.5"
                        style="min-height: 24px; max-height: 200px;"
                    ></textarea>

                    <!-- Microphone Button -->
                    <button aria-label="Voice input" class="flex-shrink-0 p-1.5 rounded-full hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                        </svg>
                    </button>

                    <!-- Send Button -->
                    <button
                        aria-label="Send message"
                        onclick={() => handleSend(inputText)}
                        disabled={!inputText.trim() || isLoading}
                        class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all {inputText.trim() && !isLoading 
                            ? 'bg-black text-white hover:bg-gray-800' 
                            : 'bg-[var(--border-light)] text-[var(--text-muted)] cursor-not-allowed'}"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Footer Text -->
            <p class="text-center text-xs text-[var(--text-muted)] mt-3">
                Virtual Realtor can make mistakes. Check important info.
            </p>
        </div>
    </div>
</div>
