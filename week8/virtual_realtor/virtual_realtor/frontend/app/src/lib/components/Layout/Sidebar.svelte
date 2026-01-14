<script lang="ts">
    import type { Snippet } from 'svelte';
    
    let { currentView = $bindable('chat'), onViewChange, footer } = $props<{
        currentView: 'chat' | 'suggestions';
        onViewChange: (view: 'chat' | 'suggestions') => void;
        footer?: Snippet;
    }>();

    function handleViewChange(view: 'chat' | 'suggestions') {
        onViewChange(view);
    }
</script>

<div class="h-full bg-[var(--sidebar-bg)] flex flex-col w-56 sm:w-64">
    <!-- Header with New Chat -->
    <div class="flex items-center justify-between px-2 py-2">
        <!-- New Chat Button -->
        <button
            onclick={() => { handleViewChange('chat'); }}
            class="flex items-center gap-2 px-3 py-1.5 rounded-md text-[var(--sidebar-text)] text-sm"
            title="New chat"
        >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            <span class="font-medium">New</span>
        </button>
    </div>

    <!-- Main Navigation -->
    <nav class="flex-1 px-2 overflow-y-auto dark-scrollbar">
        <!-- Primary Actions -->
        <div class="space-y-0.5 mt-2">
            <button
                onclick={() => handleViewChange('chat')}
                class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-left text-sm {currentView === 'chat'
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)]'
                    : 'text-[var(--sidebar-text-muted)]'}"
            >
                <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                <span>Chat</span>
            </button>

            <button
                onclick={() => handleViewChange('suggestions')}
                class="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-left text-sm {currentView === 'suggestions'
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)]'
                    : 'text-[var(--sidebar-text-muted)]'}"
            >
                <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
                <span>Properties</span>
            </button>
        </div>
    </nav>

    <!-- Footer - User Section -->
    <div class="px-2 py-2 border-t border-[var(--sidebar-border)]">
        {#if footer}
            {@render footer()}
        {/if}
    </div>
</div>
