<script lang="ts">
    import type { UserPreferences } from "$lib/types";
    import { saveUserPreferences } from "$lib/api";

    let { onSave, onCancel } = $props<{
        onSave: () => void;
        onCancel?: () => void;
    }>();

    // Form state
    let priceMin = $state("");
    let priceMax = $state("");
    let zipCode1 = $state("");
    let zipCode2 = $state("");
    let zipCode3 = $state("");
    let bedsMin = $state("");
    let bedsMax = $state("");
    let bathsMin = $state("");
    let bathsMax = $state("");
    let sqftMin = $state("");
    let sqftMax = $state("");
    let propertyType = $state("");

    // Wizard state
    let currentStep = $state(1);
    let totalSteps = 5;
    let isLoading = $state(false);
    let errorMessage = $state("");
    let validationErrors = $state<string[]>([]);

    async function handleNext() {
        validationErrors = [];
        
        if (currentStep === 1) {
            if (priceMin && priceMax && parseInt(priceMax) < parseInt(priceMin)) {
                validationErrors.push("Maximum price must be greater than minimum");
                return;
            }
        } else if (currentStep === 2) {
            const zips = [zipCode1, zipCode2, zipCode3].filter(z => z.trim());
            for (const zip of zips) {
                if (zip && (zip.length !== 5 || !zip.match(/^\d+$/))) {
                    validationErrors.push(`Invalid zip code: ${zip}. Must be 5 digits.`);
                    return;
                }
            }
        } else if (currentStep === 3) {
            if (bedsMin && bedsMax && parseInt(bedsMax) < parseInt(bedsMin)) {
                validationErrors.push("Maximum bedrooms must be greater than minimum");
                return;
            }
        } else if (currentStep === 4) {
            if (bathsMin && bathsMax && parseFloat(bathsMax) < parseFloat(bathsMin)) {
                validationErrors.push("Maximum bathrooms must be greater than minimum");
                return;
            }
        } else if (currentStep === 5) {
            if (sqftMin && sqftMax && parseInt(sqftMax) < parseInt(sqftMin)) {
                validationErrors.push("Maximum sqft must be greater than minimum");
                return;
            }
        }

        if (currentStep < totalSteps) {
            currentStep++;
        } else {
            await handleSubmit();
        }
    }

    function handleBack() {
        if (currentStep > 1) {
            currentStep--;
            validationErrors = [];
        }
    }

    async function handleSubmit() {
        console.log("=== Starting to save preferences ===");
        
        // Validate that at least one field is filled
        const hasAnyValue = priceMin || priceMax || zipCode1 || zipCode2 || zipCode3 ||
                           bedsMin || bedsMax || bathsMin || bathsMax ||
                           sqftMin || sqftMax || propertyType;
        
        if (!hasAnyValue) {
            errorMessage = "Please fill in at least one field";
            validationErrors.push("At least one preference must be set");
            currentStep = 1;
            return;
        }

        const zipCodes = [zipCode1, zipCode2, zipCode3]
            .filter((z) => z.trim())
            .map((z) => z.trim());

        // Build preferences object, excluding undefined/empty nested objects
        const preferences: Partial<UserPreferences> = {};
        
        // Only include priceRange if at least one value is set
        if (priceMin || priceMax) {
            preferences.priceRange = {};
            if (priceMin) preferences.priceRange.min = parseInt(priceMin);
            if (priceMax) preferences.priceRange.max = parseInt(priceMax);
        }
        
        // Only include zipCodes if we have any
        if (zipCodes.length > 0) {
            preferences.zipCodes = zipCodes;
        }
        
        // Only include bedrooms if at least one value is set
        if (bedsMin || bedsMax) {
            preferences.bedrooms = {};
            if (bedsMin) preferences.bedrooms.min = parseInt(bedsMin);
            if (bedsMax) preferences.bedrooms.max = parseInt(bedsMax);
        }
        
        // Only include bathrooms if at least one value is set
        if (bathsMin || bathsMax) {
            preferences.bathrooms = {};
            if (bathsMin) preferences.bathrooms.min = parseFloat(bathsMin);
            if (bathsMax) preferences.bathrooms.max = parseFloat(bathsMax);
        }
        
        // Only include sqft if at least one value is set
        if (sqftMin || sqftMax) {
            preferences.sqft = {};
            if (sqftMin) preferences.sqft.min = parseInt(sqftMin);
            if (sqftMax) preferences.sqft.max = parseInt(sqftMax);
        }
        
        // Only include propertyType if set
        if (propertyType) {
            preferences.propertyType = propertyType;
        }

        console.log("Preferences to save:", JSON.stringify(preferences, null, 2));

        isLoading = true;
        errorMessage = "";

        try {
            console.log("Calling saveUserPreferences API...");
            const result = await saveUserPreferences(preferences);
            console.log("✓ Preferences saved successfully!", result);
            console.log("Calling onSave() callback...");
            onSave();
            console.log("onSave() callback completed");
        } catch (e: any) {
            console.error("❌ Failed to save preferences:", e);
            errorMessage = e.message || "Failed to save preferences. Please try again.";
            currentStep = 1; // Go back to first step on error
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="w-full max-w-2xl mx-auto">
    <!-- Progress Bar -->
    <div class="mb-8">
        <div class="flex justify-between mb-2">
            {#each Array(totalSteps) as _, i}
                <div class="flex-1 {i < totalSteps - 1 ? 'mr-2' : ''}">
                    <div class="h-1.5 rounded-full {i < currentStep ? 'bg-[var(--color-accent-primary)]' : 'bg-[var(--color-border-secondary)]'} transition-colors"></div>
                </div>
            {/each}
        </div>
        <p class="text-sm text-[var(--text-secondary)] text-center">
            Step {currentStep} of {totalSteps}
        </p>
    </div>

    <!-- Error Messages -->
    {#if errorMessage}
        <div class="mb-6 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-lg text-sm">
            {errorMessage}
        </div>
    {/if}

    {#if validationErrors.length > 0}
        <div class="mb-6 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-lg text-sm">
            <ul class="list-disc list-inside">
                {#each validationErrors as error}
                    <li>{error}</li>
                {/each}
            </ul>
        </div>
    {/if}

    <!-- Step Content -->
    <div class="bg-[var(--bg-card)] border border-[var(--color-border-primary)] rounded-xl p-8 mb-6 shadow-sm">
        {#if currentStep === 1}
            <!-- Step 1: Budget -->
            <h3 class="text-2xl font-semibold text-[var(--text-primary)] mb-6">What's your budget?</h3>
            
            <div class="space-y-4">
                <div>
                    <label for="priceMin" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Minimum Price
                    </label>
                    <input
                        id="priceMin"
                        type="number"
                        bind:value={priceMin}
                        placeholder="e.g., 300000"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>

                <div>
                    <label for="priceMax" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Maximum Price
                    </label>
                    <input
                        id="priceMax"
                        type="number"
                        bind:value={priceMax}
                        placeholder="e.g., 800000"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>
            </div>

        {:else if currentStep === 2}
            <!-- Step 2: Location -->
            <h3 class="text-2xl font-semibold text-[var(--text-primary)] mb-6">Where are you looking?</h3>
            
            <div class="space-y-4">
                <div>
                    <label for="zipCode1" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Zip Code 1
                    </label>
                    <input
                        id="zipCode1"
                        type="text"
                        bind:value={zipCode1}
                        placeholder="e.g., 94102"
                        maxlength="5"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>

                <div>
                    <label for="zipCode2" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Zip Code 2 (Optional)
                    </label>
                    <input
                        id="zipCode2"
                        type="text"
                        bind:value={zipCode2}
                        placeholder="e.g., 94103"
                        maxlength="5"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>

                <div>
                    <label for="zipCode3" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Zip Code 3 (Optional)
                    </label>
                    <input
                        id="zipCode3"
                        type="text"
                        bind:value={zipCode3}
                        placeholder="e.g., 94104"
                        maxlength="5"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>
            </div>

        {:else if currentStep === 3}
            <!-- Step 3: Bedrooms -->
            <h3 class="text-2xl font-semibold text-[var(--text-primary)] mb-6">How many bedrooms?</h3>
            
            <div class="space-y-4">
                <div>
                    <label for="bedsMin" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Minimum Bedrooms
                    </label>
                    <input
                        id="bedsMin"
                        type="number"
                        bind:value={bedsMin}
                        placeholder="e.g., 2"
                        min="0"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>

                <div>
                    <label for="bedsMax" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Maximum Bedrooms
                    </label>
                    <input
                        id="bedsMax"
                        type="number"
                        bind:value={bedsMax}
                        placeholder="e.g., 4"
                        min="0"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>
            </div>

        {:else if currentStep === 4}
            <!-- Step 4: Bathrooms -->
            <h3 class="text-2xl font-semibold text-[var(--text-primary)] mb-6">How many bathrooms?</h3>
            
            <div class="space-y-4">
                <div>
                    <label for="bathsMin" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Minimum Bathrooms
                    </label>
                    <input
                        id="bathsMin"
                        type="number"
                        bind:value={bathsMin}
                        placeholder="e.g., 1"
                        min="0"
                        step="0.5"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>

                <div>
                    <label for="bathsMax" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Maximum Bathrooms
                    </label>
                    <input
                        id="bathsMax"
                        type="number"
                        bind:value={bathsMax}
                        placeholder="e.g., 2.5"
                        min="0"
                        step="0.5"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>
            </div>

        {:else if currentStep === 5}
            <!-- Step 5: Square Footage & Type -->
            <h3 class="text-2xl font-semibold text-[var(--text-primary)] mb-6">Property details</h3>
            
            <div class="space-y-4">
                <div>
                    <label for="sqftMin" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Minimum Square Feet
                    </label>
                    <input
                        id="sqftMin"
                        type="number"
                        bind:value={sqftMin}
                        placeholder="e.g., 1000"
                        min="0"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>

                <div>
                    <label for="sqftMax" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Maximum Square Feet
                    </label>
                    <input
                        id="sqftMax"
                        type="number"
                        bind:value={sqftMax}
                        placeholder="e.g., 3000"
                        min="0"
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-muted)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    />
                </div>

                <div>
                    <label for="propertyType" class="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Property Type (Optional)
                    </label>
                    <select
                        id="propertyType"
                        bind:value={propertyType}
                        class="w-full px-4 py-3 bg-[var(--input-bg)] text-[var(--text-primary)] rounded-lg border border-[var(--color-border-primary)] focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
                    >
                        <option value="">Any</option>
                        <option value="Single Family">Single Family</option>
                        <option value="Condo">Condo</option>
                        <option value="Townhouse">Townhouse</option>
                        <option value="Multi Family">Multi Family</option>
                    </select>
                </div>
            </div>
        {/if}
    </div>

    <!-- Navigation Buttons -->
    <div class="flex gap-3 justify-between">
        <div class="flex gap-3">
            {#if currentStep > 1}
                <button
                    onclick={handleBack}
                    type="button"
                    disabled={isLoading}
                    class="px-6 py-3 rounded-lg border border-[var(--color-border-primary)] text-[var(--text-primary)] hover:bg-[var(--bg-container)] transition-colors disabled:opacity-50 font-medium"
                >
                    Back
                </button>
            {/if}
            
            {#if onCancel && currentStep === 1}
                <button
                    onclick={onCancel}
                    type="button"
                    disabled={isLoading}
                    class="px-6 py-3 rounded-lg border border-[var(--color-border-primary)] text-[var(--text-primary)] hover:bg-[var(--bg-container)] transition-colors disabled:opacity-50 font-medium"
                >
                    Cancel
                </button>
            {/if}
        </div>

        <button
            onclick={handleNext}
            type="button"
            disabled={isLoading}
            class="px-6 py-3 rounded-lg bg-[var(--color-accent-primary)] text-white font-semibold hover:bg-[var(--color-accent-secondary)] transition-colors disabled:opacity-50 flex items-center gap-2"
        >
            {#if isLoading}
                <span class="animate-spin">⏳</span>
            {/if}
            {currentStep === totalSteps ? 'Save Preferences' : 'Next'}
        </button>
    </div>
</div>
