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

<div class="h-full bg-[var(--sidebar-bg)] flex flex-col w-64">
    <!-- Header with Logo and Toggle -->
    <div class="flex items-center justify-between p-3 pt-3">
        <!-- Sidebar Toggle -->
        <button class="p-2 rounded-lg hover:bg-[var(--sidebar-hover)] text-[var(--sidebar-text)] transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
        </button>
        
        <!-- New Chat Button -->
        <button 
            onclick={() => { handleViewChange('chat'); }}
            class="p-2 rounded-lg hover:bg-[var(--sidebar-hover)] text-[var(--sidebar-text)] transition-colors"
            title="New chat"
        >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
        </button>
    </div>
    
    <!-- Search / New Chat Action -->
    <div class="px-3 mb-2">
        <button 
            onclick={() => { handleViewChange('chat'); }}
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)] transition-colors text-sm font-medium"
        >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <span>Search</span>
        </button>
    </div>

    <!-- Main Navigation -->
    <nav class="flex-1 px-3 overflow-y-auto dark-scrollbar">
        <!-- Primary Actions -->
        <div class="space-y-0.5">
            <button
                onclick={() => handleViewChange('chat')}
                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors text-sm {currentView === 'chat' 
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)]' 
                    : 'text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)]'}"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                <span>Chat</span>
            </button>

            <button
                onclick={() => handleViewChange('suggestions')}
                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors text-sm {currentView === 'suggestions' 
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)]' 
                    : 'text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)]'}"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
                <span>Properties</span>
            </button>
        </div>

        <!-- Divider -->
        <div class="my-4 border-t border-[var(--sidebar-border)]"></div>
        
        <!-- Features Section -->
        <div class="mb-2">
            <p class="px-3 py-1.5 text-xs font-medium text-[var(--sidebar-text-muted)] uppercase tracking-wider">
                Features
            </p>
        </div>
        <div class="space-y-0.5">
            <button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)] transition-colors text-sm">
                <span class="text-lg">🏠</span>
                <span>Home Search</span>
            </button>
            <button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)] transition-colors text-sm">
                <span class="text-lg">📊</span>
                <span>Market Analysis</span>
            </button>
            <button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)] transition-colors text-sm">
                <span class="text-lg">🎯</span>
                <span>Neighborhood Guide</span>
            </button>
        </div>
    </nav>

    <!-- Footer - User Section -->
    <div class="p-3 border-t border-[var(--sidebar-border)]">
        {#if footer}
            {@render footer()}
        {/if}
    </div>
</div>
