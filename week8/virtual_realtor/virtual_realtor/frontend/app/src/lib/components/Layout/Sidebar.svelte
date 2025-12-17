<script lang="ts">
    let { currentView = $bindable('chat'), onViewChange } = $props<{
        currentView: 'chat' | 'suggestions';
        onViewChange: (view: 'chat' | 'suggestions') => void;
    }>();

    function handleViewChange(view: 'chat' | 'suggestions') {
        // Only call parent's handler - let parent update currentView
        // The bindable prop will update automatically from parent
        onViewChange(view);
    }
</script>

<div class="h-full bg-white border-r border-[var(--border-light)] flex flex-col w-56">
    <!-- Navigation Menu -->
    <nav class="flex-1 p-3 space-y-2">
        <button
            onclick={() => handleViewChange('chat')}
            class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left transition-all group {currentView === 'chat' 
                ? 'bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white shadow-lg' 
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'}"
        >
            <svg class="w-4 h-4 {currentView === 'chat' ? '' : 'group-hover:scale-110 transition-transform'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
            <div class="flex-1">
                <div class="font-semibold text-sm">Chat</div>
                <div class="text-xs opacity-90">Ask anything</div>
            </div>
        </button>

        <button
            onclick={() => handleViewChange('suggestions')}
            class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left transition-all group {currentView === 'suggestions' 
                ? 'bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white shadow-lg' 
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'}"
        >
            <svg class="w-4 h-4 {currentView === 'suggestions' ? '' : 'group-hover:scale-110 transition-transform'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
            </svg>
            <div class="flex-1">
                <div class="font-semibold text-sm">Properties</div>
                <div class="text-xs opacity-90">View listings</div>
            </div>
        </button>
    </nav>

    <!-- Footer - User Section -->
    <div class="p-4 border-t border-[var(--border-light)]">
        <slot name="footer"></slot>
    </div>
</div>
