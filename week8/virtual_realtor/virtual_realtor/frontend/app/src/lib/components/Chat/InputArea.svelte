<script lang="ts">
    let { onSend, disabled = false } = $props();
    let message = $state("");

    function handleSend() {
        if (message.trim() && !disabled) {
            onSend(message.trim());
            message = "";
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }
</script>

<div
    class="p-5 bg-white dark:bg-[#252525] border-t border-[var(--color-border-primary)] flex gap-3 transition-colors duration-300"
>
    <input
        type="text"
        bind:value={message}
        onkeydown={handleKeydown}
        {disabled}
        placeholder="Your next home just a message away..."
        class="flex-1 p-3 px-4 border-2 border-[var(--color-border-primary)] rounded-full text-base outline-none transition-all duration-300 bg-white dark:bg-[#2c2c2c] text-[#2d3436] dark:text-[#e0e0e0] focus:border-[var(--color-accent-tertiary)] focus:shadow-[0_0_0_3px_rgba(232,93,117,0.1)] disabled:opacity-60 disabled:cursor-not-allowed"
    />
    <button
        onclick={handleSend}
        disabled={disabled || !message.trim()}
        class="bg-gradient-to-br from-[var(--color-accent-tertiary)] to-[var(--color-accent-quaternary)] text-white border-none py-3 px-6 rounded-full text-base font-semibold cursor-pointer transition-transform shadow-[0_4px_15px_rgba(232,93,117,0.3)] hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(232,93,117,0.5)] disabled:bg-gray-300 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none disabled:opacity-50"
    >
        Send
    </button>
</div>
