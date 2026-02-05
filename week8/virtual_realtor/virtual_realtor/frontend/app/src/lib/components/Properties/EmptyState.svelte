<script lang="ts">
    import { Building } from 'lucide-svelte';

    let { message = "No saved properties yet", icon = "building" } = $props();
</script>

<div class="flex flex-col items-center justify-center py-12 px-4 text-center border-2 border-dashed border-gray-200 rounded-lg">
    <div class="bg-gray-50 p-4 rounded-full mb-4">
        <Building class="w-8 h-8 text-gray-400" />
    </div>
    <h3 class="text-lg font-medium text-gray-900 mb-1">{message}</h3>
    <!-- <p class="text-sm text-gray-500">Start searching to find your dream home.</p> -->
</div>
