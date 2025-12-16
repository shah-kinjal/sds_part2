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

<div class="w-64 h-screen bg-[var(--bg-sidebar)] border-r border-[var(--color-border-primary)] flex flex-col">
    <!-- Header -->
    <div class="p-4 border-b border-[var(--color-border-primary)]">
        <h1 class="text-[var(--text-primary)] text-lg font-semibold">Virtual Realtor</h1>
    </div>

    <!-- Navigation Menu -->
    <nav class="flex-1 p-3">
        <button
            onclick={() => handleViewChange('chat')}
            class="w-full px-4 py-2.5 rounded-lg mb-2 text-left transition-colors {currentView === 'chat' ? 'bg-[var(--color-accent-primary)] text-white' : 'text-[var(--text-primary)] hover:bg-[var(--bg-container)]'}"
        >
            <span class="font-medium">Chat</span>
        </button>

        <button
            onclick={() => handleViewChange('suggestions')}
            class="w-full px-4 py-2.5 rounded-lg text-left transition-colors {currentView === 'suggestions' ? 'bg-[var(--color-accent-primary)] text-white' : 'text-[var(--text-primary)] hover:bg-[var(--bg-container)]'}"
        >
            <span class="font-medium">Property Suggestions</span>
        </button>
    </nav>

    <!-- Footer - User Info -->
    <div class="p-3 border-t border-[var(--color-border-primary)]">
        <slot name="footer"></slot>
    </div>
</div>

