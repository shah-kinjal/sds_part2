<script lang="ts">
    import { marked } from "marked";

    let { msg } = $props();

    // msg structure: { role: 'assistant' | 'user', content: string }
    let isUser = $derived(msg.role === "user");
</script>

<div class="mb-4 flex items-start {isUser ? 'justify-end' : ''}">
    <div
        class="max-w-[70%] p-3 px-4 rounded-[18px] break-words leading-relaxed transition-colors duration-300
        {isUser
            ? 'bg-gradient-to-br from-[var(--color-msg-user-start)] to-[var(--color-msg-user-end)] text-[#2d3436] rounded-br-md border border-[var(--color-border-secondary)]'
            : 'bg-gradient-to-br from-[var(--color-msg-assistant-start)] to-[var(--color-msg-assistant-end)] text-[#2d3436] rounded-bl-md border border-[var(--color-border-primary)]'}"
    >
        <div
            class="text-xs font-semibold mb-1 opacity-70 text-[rgba(45,52,54,0.8)]"
        >
            {isUser ? "You" : "Assistant"}
        </div>
        <div class="prose prose-sm max-w-none">
            {@html marked.parse(msg.content)}
        </div>
    </div>
</div>
