<script lang="ts">
    import type { Snippet } from "svelte";
    import { page } from "$app/stores";
    import { Building, Heart, Calendar, MessageSquare } from "lucide-svelte";

    let { footer } = $props<{
        footer?: Snippet;
    }>();

    // Derived state for active view based on URL
    let currentPath = $derived($page.url.pathname);
    let currentViewParam = $derived($page.url.searchParams.get("view"));

    // Helper to check active state
    function isActive(path: string, viewParam?: string): boolean {
        if (path === "/" && viewParam) {
            return currentPath === "/" && currentViewParam === viewParam;
        }
        if (path === "/" && !viewParam) {
            // Default home is chat if no view param or view=chat
            return (
                currentPath === "/" &&
                (!currentViewParam || currentViewParam === "chat")
            );
        }
        return currentPath.startsWith(path);
    }
</script>

<div
    class="h-full bg-[var(--sidebar-bg)] flex flex-col w-56 sm:w-64 border-r border-[var(--sidebar-border)]"
>
    <!-- Header with New Chat -->
    <div class="flex items-center justify-between px-3 py-3">
        <!-- New Chat Button -->
        <a
            href="/"
            class="flex items-center gap-2 px-3 py-1.5 rounded-md text-[var(--sidebar-text)] text-sm hover:bg-[var(--sidebar-hover)] transition-colors"
            title="New chat"
        >
            <MessageSquare class="w-4 h-4" />
            <span class="font-medium">New Chat</span>
        </a>
    </div>

    <!-- Main Navigation -->
    <nav class="flex-1 px-3 overflow-y-auto dark-scrollbar py-2 space-y-4">
        <!-- Primary Actions -->
        <div class="space-y-1">
            <h3
                class="px-2 text-xs font-semibold text-[var(--sidebar-text-muted)] uppercase tracking-wider mb-2"
            >
                Discover
            </h3>

            <a
                href="/"
                class="w-full flex items-center gap-3 px-2 py-2 rounded-md text-left text-sm transition-colors {isActive(
                    '/',
                    'chat',
                )
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)] font-medium'
                    : 'text-[var(--sidebar-text-muted)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--sidebar-text)]'}"
            >
                <MessageSquare class="w-4 h-4" />
                <span>Chat Assistant</span>
            </a>

            <a
                href="/?view=suggestions"
                class="w-full flex items-center gap-3 px-2 py-2 rounded-md text-left text-sm transition-colors {isActive(
                    '/',
                    'suggestions',
                )
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)] font-medium'
                    : 'text-[var(--sidebar-text-muted)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--sidebar-text)]'}"
            >
                <Building class="w-4 h-4" />
                <span>Properties</span>
            </a>
        </div>

        <!-- Saved Stuff -->
        <div class="space-y-1">
            <h3
                class="px-2 text-xs font-semibold text-[var(--sidebar-text-muted)] uppercase tracking-wider mb-2"
            >
                Saved
            </h3>

            <a
                href="/favorites"
                class="w-full flex items-center gap-3 px-2 py-2 rounded-md text-left text-sm transition-colors {isActive(
                    '/favorites',
                )
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)] font-medium'
                    : 'text-[var(--sidebar-text-muted)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--sidebar-text)]'}"
            >
                <Heart class="w-4 h-4" />
                <span>My Favorites</span>
            </a>

            <a
                href="/visit-list"
                class="w-full flex items-center gap-3 px-2 py-2 rounded-md text-left text-sm transition-colors {isActive(
                    '/visit-list',
                )
                    ? 'bg-[var(--sidebar-active)] text-[var(--sidebar-text)] font-medium'
                    : 'text-[var(--sidebar-text-muted)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--sidebar-text)]'}"
            >
                <Calendar class="w-4 h-4" />
                <span>Visit List</span>
            </a>
        </div>
    </nav>

    <!-- Footer - User Section -->
    <div
        class="px-3 py-3 border-t border-[var(--sidebar-border)] bg-[var(--sidebar-bg)]"
    >
        {#if footer}
            {@render footer()}
        {/if}
    </div>
</div>
