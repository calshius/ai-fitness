<script>
    import { createEventDispatcher } from 'svelte';
    import { chatStore } from '$lib/stores/chatStore';
    
    const dispatch = createEventDispatcher();
    
    let query = '';
    let inputHeight = 56; // Default height
    let textarea;
    
    // Model options
    const modelOptions = [
        // Most Capable (but may be slower)
        { value: "mistralai/Mistral-7B-Instruct-v0.2", label: "Mistral 7B (Default)", category: "Most Capable" },
        { value: "tiiuae/falcon-7b-instruct", label: "Falcon 7B", category: "Most Capable" },
        
        // Balanced (good performance/speed tradeoff)
        { value: "tiiuae/falcon-rw-1b", label: "Falcon 1B", category: "Balanced" },
        { value: "databricks/dolly-v2-3b", label: "Dolly v2 3B", category: "Balanced" },
        
        // Fastest (may be less accurate)
        { value: "google/flan-t5-large", label: "Flan-T5 Large", category: "Fastest" },
        { value: "microsoft/phi-1_5", label: "Phi-1.5", category: "Fastest" },
        { value: "TinyLlama/TinyLlama-1.1B-Chat-v1.0", label: "TinyLlama 1.1B", category: "Fastest" }
    ];
    
    // Group models by category
    const groupedModels = modelOptions.reduce((acc, model) => {
        if (!acc[model.category]) {
            acc[model.category] = [];
        }
        acc[model.category].push(model);
        return acc;
    }, {});
    
    // Model selection dropdown state
    let showModelDropdown = false;
    
    function handleSubmit() {
        if (query.trim() && !$chatStore.isLoading) {
            dispatch('submit', query);
            query = '';
            // Reset textarea height
            if (textarea) {
                textarea.style.height = '56px';
                inputHeight = 56;
            }
        }
    }
    
    function handleKeydown(event) {
        // Submit on Enter (without Shift)
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSubmit();
        }
    }
    
    function autoResize() {
        if (textarea) {
            // Reset height to auto to get the correct scrollHeight
            textarea.style.height = 'auto';
            // Set new height based on scrollHeight (with min height of 56px)
            const newHeight = Math.max(56, textarea.scrollHeight);
            textarea.style.height = `${newHeight}px`;
            inputHeight = newHeight;
        }
    }
    
    function selectModel(model) {
        chatStore.setModel(model.value);
        showModelDropdown = false;
    }
    
    // Close dropdown when clicking outside
    function handleClickOutside(event) {
        if (showModelDropdown && !event.target.closest('.model-selector')) {
            showModelDropdown = false;
        }
    }
    
    // Get current model label
    $: currentModel = modelOptions.find(m => m.value === $chatStore.selectedModel) || modelOptions[0];
</script>

<svelte:window on:click={handleClickOutside} />

<div class="input-container" style="--input-height: {inputHeight}px">
    <textarea
        bind:this={textarea}
        bind:value={query}
        on:keydown={handleKeydown}
        on:input={autoResize}
        placeholder="Ask about your fitness data..."
        disabled={$chatStore.isLoading}
        rows="1"
    ></textarea>
    
    <div class="right-controls">
        <div class="model-selector">
            <button 
                class="model-button" 
                on:click={() => showModelDropdown = !showModelDropdown}
                disabled={$chatStore.isLoading}
                title="Select AI model"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2a4 4 0 0 1 4 4v4a4 4 0 0 1-4 4 4 4 0 0 1-4-4V6a4 4 0 0 1 4-4z"></path>
                    <path d="M18 8a4 4 0 0 1 4 4v2a4 4 0 0 1-4 4 4 4 0 0 1-4-4v-2a4 4 0 0 1 4-4z"></path>
                    <path d="M6 8a4 4 0 0 1 4 4v2a4 4 0 0 1-4 4 4 4 0 0 1-4-4v-2a4 4 0 0 1 4-4z"></path>
                </svg>
                <span class="model-name">{currentModel.label.split(' ')[0]}</span>
            </button>
            
            {#if showModelDropdown}
                <div class="model-dropdown">
                    {#each Object.entries(groupedModels) as [category, models]}
                        <div class="model-category">
                            <div class="category-label">{category}</div>
                            {#each models as model}
                                <button 
                                    class="model-option {$chatStore.selectedModel === model.value ? 'selected' : ''}" 
                                    on:click={() => selectModel(model)}
                                >
                                    {model.label}
                                </button>
                            {/each}
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
        
        <button 
            class="send-button"
            on:click={handleSubmit} 
            disabled={!query.trim() || $chatStore.isLoading}
            class:loading={$chatStore.isLoading}
        >
            {#if $chatStore.isLoading}
                <div class="spinner"></div>
            {:else}
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            {/if}
        </button>
    </div>
</div>

<style>
    .input-container {
        display: flex;
        align-items: center;
        background-color: white;
        border-radius: 1.5rem;
        padding: 0.75rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        margin: 1rem 0;
        position: relative;
    }

    textarea {
        flex: 1;
        border: none;
        outline: none;
        resize: none;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        font-family: inherit;
        height: var(--input-height);
        max-height: 200px;
        overflow-y: auto;
    }
    
    .right-controls {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .send-button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s;
        flex-shrink: 0;
    }

    .send-button:hover:not(:disabled) {
        background-color: #2563eb;
    }

    .send-button:disabled {
        background-color: #93c5fd;
        cursor: not-allowed;
    }

    .loading {
        position: relative;
    }

    .spinner {
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
    
    /* Model selector styles */
    .model-selector {
        position: relative;
    }
    
    .model-button {
        background-color: #f3f4f6;
        color: #4b5563;
        border-radius: 1rem;
        width: auto;
        height: 36px;
        padding: 0 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-shrink: 0;
    }
    
    .model-button:hover:not(:disabled) {
        background-color: #e5e7eb;
    }
    
    .model-name {
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .model-dropdown {
        position: absolute;
        bottom: calc(100% + 0.5rem); /* Position above the button */
        right: 0; /* Align to the right */
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        width: 250px;
        max-height: 400px;
        overflow-y: auto;
        z-index: 10;
        padding: 0.5rem;
    }
    
    .model-category {
        margin-bottom: 0.5rem;
    }
    
    .category-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6b7280;
        padding: 0.5rem;
        text-transform: uppercase;
    }
    
    .model-option {
        width: 100%;
        text-align: left;
        background-color: transparent;
        color: #374151;
        border-radius: 0.25rem;
        height: auto;
        padding: 0.5rem;
        margin-bottom: 0.25rem;
        font-size: 0.875rem;
    }
    
    .model-option:hover {
        background-color: #f3f4f6;
    }
    
    .model-option.selected {
        background-color: #eff6ff;
        color: #3b82f6;
    }
</style>
